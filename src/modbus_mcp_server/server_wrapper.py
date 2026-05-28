"""Modbus server wrapper providing datastore CRUD and lifecycle management."""

import asyncio
import logging
import threading
from typing import List, Optional, Union

from pymodbus.datastore import (
    ModbusDeviceContext,
    ModbusServerContext,
)
from pymodbus.server import ModbusTcpServer, ModbusSerialServer
from pymodbus.framer import FramerType

from .alias_manager import AliasManager
from .auditing_datastore import AuditingDataBlock
from .models import RegisterType, ServerTCPParams, ServerRTUParams
from .operation_log import OperationLog
from .validation import ModbusValidator

logger = logging.getLogger(__name__)

# Datastore function codes used by pymodbus
_FC_DISCRETE_INPUTS = 2
_FC_COILS = 1
_FC_INPUT_REGISTERS = 4
_FC_HOLDING_REGISTERS = 3


class ModbusServerWrapper:
    """Wrapper around a pymodbus server with datastore CRUD operations.

    The pymodbus 3.x server is fully async. To avoid conflicts with the
    MCP framework's own event loop, each server runs in a dedicated thread
    with its own event loop. Both server construction and serve_forever()
    happen inside that thread. Datastore CRUD operations are synchronous
    since they only access the in-memory context objects.
    """

    def __init__(
        self,
        context: ModbusServerContext,
        server_type: str,
        slave_id: int,
    ):
        """Initialize the server wrapper.

        Args:
            context: The ModbusServerContext holding datastores
            server_type: "TCP" or "RTU"
            slave_id: The slave ID this server responds as
        """
        self.server: Optional[Union[ModbusTcpServer, ModbusSerialServer]] = None
        self.context = context
        self.server_type = server_type
        self.slave_id = slave_id
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._task: Optional[asyncio.Task] = None
        self._thread: Optional[threading.Thread] = None
        self._running = False
        self._lock = threading.RLock()
        self._start_error: Optional[Exception] = None

    def _start_tcp(self, params: ServerTCPParams) -> None:
        """Start a TCP server in a background thread with its own event loop.

        Args:
            params: TCP server parameters

        Raises:
            ValueError: If the server fails to start
        """
        ready = threading.Event()

        async def run_async_server():
            try:
                self.server = ModbusTcpServer(
                    context=self.context,
                    address=(params.host, params.port),
                )
                ready.set()
                await self.server.serve_forever()
            except asyncio.CancelledError:
                logger.info(f"TCP server (slave {self.slave_id}) task cancelled")
            except Exception as e:
                self._start_error = e
                ready.set()
                logger.error(f"TCP server error: {e}")
                self._running = False

        def run_server():
            try:
                self._loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self._loop)
                self._task = self._loop.create_task(run_async_server())
                self._loop.run_until_complete(self._task)
            except Exception as e:
                self._start_error = self._start_error or e
                ready.set()
                logger.error(f"Event loop error: {e}")
            finally:
                self._loop.close()
                self._loop = None

        self._thread = threading.Thread(target=run_server, daemon=True)
        self._running = True
        self._thread.start()

        # Wait for the server to be created (or fail)
        ready.wait(timeout=10.0)
        if self._start_error:
            self._running = False
            error = self._start_error
            self._start_error = None
            raise ValueError(f"Failed to start TCP server: {error}")

        logger.info(f"TCP server (slave {self.slave_id}) started on {params.host}:{params.port}")

    def _start_rtu(self, params: ServerRTUParams) -> None:
        """Start an RTU server in a background thread with its own event loop.

        Args:
            params: RTU server parameters

        Raises:
            ValueError: If the server fails to start
        """
        ready = threading.Event()

        async def run_async_server():
            try:
                self.server = ModbusSerialServer(
                    context=self.context,
                    framer=FramerType.RTU,
                    port=params.port,
                    baudrate=params.baudrate,
                    bytesize=params.bytesize,
                    parity=params.parity,
                    stopbits=params.stopbits,
                    timeout=params.timeout,
                )
                ready.set()
                await self.server.serve_forever()
            except asyncio.CancelledError:
                logger.info(f"RTU server (slave {self.slave_id}) task cancelled")
            except Exception as e:
                self._start_error = e
                ready.set()
                logger.error(f"RTU server error: {e}")
                self._running = False

        def run_server():
            try:
                self._loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self._loop)
                self._task = self._loop.create_task(run_async_server())
                self._loop.run_until_complete(self._task)
            except Exception as e:
                self._start_error = self._start_error or e
                ready.set()
                logger.error(f"Event loop error: {e}")
            finally:
                self._loop.close()
                self._loop = None

        self._thread = threading.Thread(target=run_server, daemon=True)
        self._running = True
        self._thread.start()

        # Wait for the server to be created (or fail)
        ready.wait(timeout=10.0)
        if self._start_error:
            self._running = False
            error = self._start_error
            self._start_error = None
            raise ValueError(f"Failed to start RTU server: {error}")

        logger.info(f"RTU server (slave {self.slave_id}) started on {params.port}")

    def stop(self) -> None:
        """Stop the server."""
        with self._lock:
            if not self._running:
                return
            try:
                if self._loop and self._loop.is_running() and self.server:
                    future = asyncio.run_coroutine_threadsafe(
                        self._shutdown_server(), self._loop
                    )
                    future.result(timeout=5.0)
            except Exception as e:
                logger.error(f"Error shutting down {self.server_type} server: {e}")
            finally:
                self._running = False
                if self._thread and self._thread.is_alive():
                    self._thread.join(timeout=3.0)
                self.server = None
                self._task = None
                logger.info(f"{self.server_type} server (slave {self.slave_id}) stopped")

    async def _shutdown_server(self) -> None:
        """Shutdown the server instance and wait for the task to complete."""
        if self.server:
            await self.server.shutdown()
        if self._task and not self._task.done():
            try:
                await self._task
            except Exception as e:
                logger.debug(f"Server task completion: {e}")

    def is_running(self) -> bool:
        """Check if the server is running."""
        with self._lock:
            return self._running

    # ── Datastore CRUD ──────────────────────────────────────────────

    def read_coils(self, address: int, count: int) -> List[bool]:
        """Read coil values from the local datastore."""
        with self._lock:
            ModbusValidator.validate_coil_read_params(address, count)
            device_ctx = self.context[self.slave_id]
            values = device_ctx.getValues(_FC_COILS, address, count=count)
            return [bool(v) for v in values]

    def write_coils(self, address: int, values: List[bool]) -> None:
        """Write coil values to the local datastore."""
        with self._lock:
            ModbusValidator.validate_coil_write_params(address, values)
            device_ctx = self.context[self.slave_id]
            device_ctx.setValues(_FC_COILS, address, [int(v) for v in values])

    def read_discrete_inputs(self, address: int, count: int) -> List[bool]:
        """Read discrete input values from the local datastore."""
        with self._lock:
            ModbusValidator.validate_discrete_input_read_params(address, count)
            device_ctx = self.context[self.slave_id]
            values = device_ctx.getValues(_FC_DISCRETE_INPUTS, address, count=count)
            return [bool(v) for v in values]

    def write_discrete_inputs(self, address: int, values: List[bool]) -> None:
        """Write discrete input values to the local datastore (server-side populate)."""
        with self._lock:
            ModbusValidator.validate_discrete_input_write_params(address, values)
            device_ctx = self.context[self.slave_id]
            device_ctx.setValues(_FC_DISCRETE_INPUTS, address, [int(v) for v in values])

    def read_holding_registers(self, address: int, count: int) -> List[int]:
        """Read holding register values from the local datastore."""
        with self._lock:
            ModbusValidator.validate_holding_register_read_params(address, count)
            device_ctx = self.context[self.slave_id]
            return list(device_ctx.getValues(_FC_HOLDING_REGISTERS, address, count=count))

    def write_holding_registers(self, address: int, values: List[int]) -> None:
        """Write holding register values to the local datastore."""
        with self._lock:
            ModbusValidator.validate_holding_register_write_params(address, values)
            device_ctx = self.context[self.slave_id]
            device_ctx.setValues(_FC_HOLDING_REGISTERS, address, values)

    def read_input_registers(self, address: int, count: int) -> List[int]:
        """Read input register values from the local datastore."""
        with self._lock:
            ModbusValidator.validate_input_register_read_params(address, count)
            device_ctx = self.context[self.slave_id]
            return list(device_ctx.getValues(_FC_INPUT_REGISTERS, address, count=count))

    def write_input_registers(self, address: int, values: List[int]) -> None:
        """Write input register values to the local datastore (server-side populate)."""
        with self._lock:
            ModbusValidator.validate_input_register_write_params(address, values)
            device_ctx = self.context[self.slave_id]
            device_ctx.setValues(_FC_INPUT_REGISTERS, address, values)

    # ── Factory methods ─────────────────────────────────────────────

    @classmethod
    def create_tcp_server(
        cls,
        params: ServerTCPParams,
        slave_id: int,
        operation_log: OperationLog,
        alias_manager: AliasManager,
        server_id: str,
    ) -> "ModbusServerWrapper":
        """Create and start a Modbus TCP server.

        The server is created and started inside a dedicated background thread
        with its own event loop, avoiding conflicts with any running event loop
        in the calling thread (e.g., the MCP framework's loop).

        Args:
            params: TCP server parameters
            slave_id: Slave ID this server responds as
            operation_log: Shared OperationLog for auditing
            alias_manager: Shared AliasManager for alias resolution
            server_id: Unique server identifier for log entries

        Returns:
            A running ModbusServerWrapper
        """
        ModbusValidator.validate_slave_id(slave_id)
        context = cls._build_context(slave_id, operation_log, alias_manager, server_id)
        wrapper = cls(context, "TCP", slave_id)
        wrapper._start_tcp(params)
        return wrapper

    @classmethod
    def create_rtu_server(
        cls,
        params: ServerRTUParams,
        slave_id: int,
        operation_log: OperationLog,
        alias_manager: AliasManager,
        server_id: str,
    ) -> "ModbusServerWrapper":
        """Create and start a Modbus RTU server.

        The server is created and started inside a dedicated background thread
        with its own event loop, avoiding conflicts with any running event loop
        in the calling thread (e.g., the MCP framework's loop).

        Args:
            params: RTU server parameters
            slave_id: Slave ID this server responds as
            operation_log: Shared OperationLog for auditing
            alias_manager: Shared AliasManager for alias resolution
            server_id: Unique server identifier for log entries

        Returns:
            A running ModbusServerWrapper
        """
        ModbusValidator.validate_slave_id(slave_id)
        context = cls._build_context(slave_id, operation_log, alias_manager, server_id)
        wrapper = cls(context, "RTU", slave_id)
        wrapper._start_rtu(params)
        return wrapper

    @staticmethod
    def _build_context(
        slave_id: int,
        operation_log: OperationLog,
        alias_manager: AliasManager,
        server_id: str,
    ) -> ModbusServerContext:
        """Build a ModbusServerContext with auditing datastores.

        Args:
            slave_id: The slave ID to register
            operation_log: Shared OperationLog for auditing
            alias_manager: Shared AliasManager for alias resolution
            server_id: Unique server identifier for log entries

        Returns:
            ModbusServerContext with AuditingDataBlock instances
        """
        # Each block: 65536 addresses initialised to 0, starting at address 0
        device_ctx = ModbusDeviceContext(
            di=AuditingDataBlock(0, [0] * 65536, operation_log, alias_manager, server_id, RegisterType.discrete_inputs),
            co=AuditingDataBlock(0, [0] * 65536, operation_log, alias_manager, server_id, RegisterType.coils),
            hr=AuditingDataBlock(0, [0] * 65536, operation_log, alias_manager, server_id, RegisterType.holding_registers),
            ir=AuditingDataBlock(0, [0] * 65536, operation_log, alias_manager, server_id, RegisterType.input_registers),
        )
        return ModbusServerContext(devices={slave_id: device_ctx}, single=False)
