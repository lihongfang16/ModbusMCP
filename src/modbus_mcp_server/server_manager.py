"""Manager for Modbus server (slave) instances."""

import logging
import threading
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Set

from .models import ServerInfo, ServerTCPParams, ServerRTUParams
from .server_wrapper import ModbusServerWrapper
from .validation import ModbusValidator

logger = logging.getLogger(__name__)


class ServerManager:
    """Manages Modbus server (slave) instances and resources."""

    def __init__(self):
        """Initialize the server manager."""
        self.servers: Dict[str, ModbusServerWrapper] = {}
        self.server_info: Dict[str, ServerInfo] = {}
        self.used_ports: Set[str] = set()  # Serial ports
        self.used_tcp_ports: Set[int] = set()  # TCP ports
        self._lock = threading.RLock()

        logger.info("ServerManager initialized")

    def create_tcp_server(self, host: str = "0.0.0.0", port: int = 502, slave_id: int = 1) -> str:
        """Create a Modbus TCP server and return its unique ID.

        Args:
            host: IP address to bind to (default: "0.0.0.0")
            port: TCP port to listen on (default: 502)
            slave_id: Modbus slave ID (1-247)

        Returns:
            Unique server identifier string

        Raises:
            ValueError: If parameters are invalid, port is in use, or server fails to start
        """
        with self._lock:
            ModbusValidator.validate_slave_id(slave_id)

            if port in self.used_tcp_ports:
                raise ValueError(f"TCP port {port} is already in use by another server")

            try:
                tcp_params = ServerTCPParams(host=host, port=port)
            except ValueError as e:
                raise ValueError(f"Invalid TCP server parameters: {e}")

            server_id = self._generate_server_id()

            try:
                wrapper = ModbusServerWrapper.create_tcp_server(tcp_params, slave_id)

                self.servers[server_id] = wrapper
                self.used_tcp_ports.add(port)

                self.server_info[server_id] = ServerInfo(
                    server_id=server_id,
                    server_type="TCP",
                    connection_params={"host": host, "port": port},
                    slave_id=slave_id,
                    created_at=datetime.now(),
                    running=True,
                )

                logger.info(f"Created TCP server {server_id} on {host}:{port}, slave {slave_id}")
                return server_id

            except Exception as e:
                # Clean up on failure
                if server_id in self.servers:
                    try:
                        self.servers[server_id].stop()
                    except Exception:
                        pass
                    del self.servers[server_id]
                if server_id in self.server_info:
                    del self.server_info[server_id]
                if port in self.used_tcp_ports:
                    self.used_tcp_ports.remove(port)

                logger.error(f"Failed to create TCP server: {e}")
                raise ValueError(f"Failed to create TCP server on {host}:{port}: {e}")

    def create_rtu_server(self, port: str, baudrate: int, slave_id: int = 1) -> str:
        """Create a Modbus RTU server and return its unique ID.

        Args:
            port: Serial port name (e.g., 'COM1', '/dev/ttyUSB0')
            baudrate: Serial communication baud rate
            slave_id: Modbus slave ID (1-247)

        Returns:
            Unique server identifier string

        Raises:
            ValueError: If parameters are invalid, port is in use, or server fails to start
        """
        with self._lock:
            ModbusValidator.validate_slave_id(slave_id)

            if port in self.used_ports:
                raise ValueError(f"Serial port {port} is already in use by another server")

            try:
                rtu_params = ServerRTUParams(port=port, baudrate=baudrate)
            except ValueError as e:
                raise ValueError(f"Invalid RTU server parameters: {e}")

            server_id = self._generate_server_id()

            try:
                wrapper = ModbusServerWrapper.create_rtu_server(rtu_params, slave_id)

                self.servers[server_id] = wrapper
                self.used_ports.add(port)

                self.server_info[server_id] = ServerInfo(
                    server_id=server_id,
                    server_type="RTU",
                    connection_params={
                        "port": port,
                        "baudrate": baudrate,
                        "bytesize": rtu_params.bytesize,
                        "parity": rtu_params.parity,
                        "stopbits": rtu_params.stopbits,
                        "timeout": rtu_params.timeout,
                    },
                    slave_id=slave_id,
                    created_at=datetime.now(),
                    running=True,
                )

                logger.info(f"Created RTU server {server_id} on {port}, slave {slave_id}")
                return server_id

            except Exception as e:
                # Clean up on failure
                if server_id in self.servers:
                    try:
                        self.servers[server_id].stop()
                    except Exception:
                        pass
                    del self.servers[server_id]
                if server_id in self.server_info:
                    del self.server_info[server_id]
                if port in self.used_ports:
                    self.used_ports.remove(port)

                logger.error(f"Failed to create RTU server: {e}")
                raise ValueError(f"Failed to create RTU server on {port}: {e}")

    def stop_server(self, server_id: str) -> bool:
        """Stop and remove a server instance.

        Args:
            server_id: Unique identifier of the server to stop

        Returns:
            True if server was stopped, False if not found
        """
        with self._lock:
            if server_id not in self.servers:
                logger.warning(f"Attempted to stop non-existent server: {server_id}")
                return False

            try:
                wrapper = self.servers[server_id]
                info = self.server_info[server_id]

                wrapper.stop()

                # Release port resources
                if info.server_type == "RTU":
                    serial_port = info.connection_params.get("port")
                    if serial_port and serial_port in self.used_ports:
                        self.used_ports.remove(serial_port)
                elif info.server_type == "TCP":
                    tcp_port = info.connection_params.get("port")
                    if tcp_port and tcp_port in self.used_tcp_ports:
                        self.used_tcp_ports.remove(tcp_port)

                del self.servers[server_id]
                del self.server_info[server_id]

                logger.info(f"Stopped and removed server {server_id}")
                return True

            except Exception as e:
                logger.error(f"Error stopping server {server_id}: {e}")
                # Still try to clean up
                try:
                    info = self.server_info.get(server_id)
                    if info and info.server_type == "RTU":
                        serial_port = info.connection_params.get("port")
                        if serial_port and serial_port in self.used_ports:
                            self.used_ports.remove(serial_port)
                    elif info and info.server_type == "TCP":
                        tcp_port = info.connection_params.get("port")
                        if tcp_port and tcp_port in self.used_tcp_ports:
                            self.used_tcp_ports.remove(tcp_port)

                    if server_id in self.servers:
                        del self.servers[server_id]
                    if server_id in self.server_info:
                        del self.server_info[server_id]
                except Exception:
                    pass
                return False

    def get_server(self, server_id: str) -> Optional[ModbusServerWrapper]:
        """Retrieve a server wrapper by ID.

        Args:
            server_id: Unique identifier of the server

        Returns:
            ModbusServerWrapper instance or None if not found
        """
        with self._lock:
            return self.servers.get(server_id)

    def list_servers(self) -> List[ServerInfo]:
        """List all server instances.

        Returns:
            List of ServerInfo objects for all servers
        """
        with self._lock:
            # Update running status
            for server_id, wrapper in self.servers.items():
                if server_id in self.server_info:
                    self.server_info[server_id].running = wrapper.is_running()

            return list(self.server_info.values())

    def cleanup_all(self) -> None:
        """Stop all servers and release all resources."""
        with self._lock:
            logger.info("Cleaning up all server instances")

            server_ids = list(self.servers.keys())
            for server_id in server_ids:
                try:
                    self.stop_server(server_id)
                except Exception as e:
                    logger.error(f"Error during cleanup of server {server_id}: {e}")

            self.servers.clear()
            self.server_info.clear()
            self.used_ports.clear()
            self.used_tcp_ports.clear()

            logger.info("Server cleanup completed")

    def _generate_server_id(self) -> str:
        """Generate a unique server identifier."""
        while True:
            server_id = str(uuid.uuid4())
            if server_id not in self.servers:
                return server_id
