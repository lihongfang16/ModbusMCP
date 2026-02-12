"""Command handlers for Modbus server (slave) operations."""

import logging
from typing import Any, Dict, List, Union

from .server_manager import ServerManager
from .validation import ModbusValidator

logger = logging.getLogger(__name__)


class ModbusServerCommandHandlers:
    """Handles MCP tool commands for Modbus server operations."""

    def __init__(self, server_manager: ServerManager):
        """Initialize command handlers with server manager.

        Args:
            server_manager: ServerManager instance for server management
        """
        self.server_manager = server_manager
        logger.info("ModbusServerCommandHandlers initialized")

    # ── Lifecycle handlers ─────────────────────────────────────────

    def handle_create_tcp_server(self, host: str = "0.0.0.0", port: int = 502, slave_id: int = 1) -> Dict[str, Any]:
        """Handle TCP server creation.

        Args:
            host: IP address to bind to
            port: TCP port to listen on
            slave_id: Modbus slave ID

        Returns:
            Dictionary with success status and server ID or error information
        """
        try:
            if not isinstance(host, str) or not host.strip():
                return self._validation_error("Host must be a non-empty string", "host", host)

            if not isinstance(port, int):
                return self._validation_error("Port must be an integer", "port", port)

            if not isinstance(slave_id, int):
                return self._validation_error("Slave ID must be an integer", "slave_id", slave_id)

            server_id = self.server_manager.create_tcp_server(host, port, slave_id)

            logger.info(f"Created TCP server {server_id} on {host}:{port}")
            return {
                "success": True,
                "server_id": server_id,
                "message": f"TCP server created successfully on {host}:{port}",
            }

        except ValueError as e:
            logger.warning(f"Validation error creating TCP server: {e}")
            return {
                "success": False,
                "error": {"code": "VALIDATION_ERROR", "message": str(e)},
            }
        except Exception as e:
            logger.error(f"Error creating TCP server: {e}")
            return {
                "success": False,
                "error": {"code": "SERVER_CREATION_ERROR", "message": f"Failed to create TCP server: {str(e)}"},
            }

    def handle_create_rtu_server(self, port: str, baudrate: int, slave_id: int = 1) -> Dict[str, Any]:
        """Handle RTU server creation.

        Args:
            port: Serial port name
            baudrate: Serial communication baud rate
            slave_id: Modbus slave ID

        Returns:
            Dictionary with success status and server ID or error information
        """
        try:
            if not isinstance(port, str) or not port.strip():
                return self._validation_error("Port must be a non-empty string", "port", port)

            if not isinstance(baudrate, int):
                return self._validation_error("Baudrate must be an integer", "baudrate", baudrate)

            if not isinstance(slave_id, int):
                return self._validation_error("Slave ID must be an integer", "slave_id", slave_id)

            server_id = self.server_manager.create_rtu_server(port, baudrate, slave_id)

            logger.info(f"Created RTU server {server_id} on {port}")
            return {
                "success": True,
                "server_id": server_id,
                "message": f"RTU server created successfully on {port}",
            }

        except ValueError as e:
            logger.warning(f"Validation error creating RTU server: {e}")
            return {
                "success": False,
                "error": {"code": "VALIDATION_ERROR", "message": str(e)},
            }
        except Exception as e:
            logger.error(f"Error creating RTU server: {e}")
            return {
                "success": False,
                "error": {"code": "SERVER_CREATION_ERROR", "message": f"Failed to create RTU server: {str(e)}"},
            }

    def handle_stop_server(self, server_id: str) -> Dict[str, Any]:
        """Handle server stop request.

        Args:
            server_id: Unique identifier of the server to stop

        Returns:
            Dictionary with success status and message
        """
        try:
            if not isinstance(server_id, str) or not server_id.strip():
                return self._validation_error("Server ID must be a non-empty string", "server_id", server_id)

            if not self.server_manager.get_server(server_id):
                return self._server_not_found_error(server_id)

            success = self.server_manager.stop_server(server_id)

            if success:
                logger.info(f"Stopped server {server_id}")
                return {
                    "success": True,
                    "message": f"Server {server_id} stopped successfully",
                }
            else:
                return {
                    "success": False,
                    "error": {"code": "SERVER_STOP_ERROR", "message": f"Failed to stop server {server_id}"},
                }

        except Exception as e:
            logger.error(f"Error stopping server {server_id}: {e}")
            return {
                "success": False,
                "error": {"code": "SERVER_STOP_ERROR", "message": f"Failed to stop server: {str(e)}"},
            }

    def handle_list_servers(self) -> Dict[str, Any]:
        """Handle listing all server instances.

        Returns:
            Dictionary with success status and server information
        """
        try:
            servers = self.server_manager.list_servers()

            server_data = []
            for server in servers:
                server_data.append({
                    "server_id": server.server_id,
                    "server_type": server.server_type,
                    "connection_params": server.connection_params,
                    "slave_id": server.slave_id,
                    "created_at": server.created_at.isoformat(),
                    "running": server.running,
                })

            return {
                "success": True,
                "servers": server_data,
            }

        except Exception as e:
            logger.error(f"Error listing servers: {e}")
            return {
                "success": False,
                "error": {"code": "SERVER_LIST_ERROR", "message": f"Failed to list servers: {str(e)}"},
            }

    # ── Datastore CRUD handlers ────────────────────────────────────

    def handle_server_read_coils(self, server_id: str, address: int, count: int) -> Dict[str, Any]:
        """Handle reading coils from a server's local datastore.

        Args:
            server_id: Server identifier
            address: Starting address
            count: Number of coils to read

        Returns:
            Dictionary with success status and coil values or error information
        """
        try:
            validation = self._validate_read_params(server_id, address, count)
            if not validation["success"]:
                return validation

            server = self.server_manager.get_server(server_id)
            if not server:
                return self._server_not_found_error(server_id)

            data = server.read_coils(address, count)
            return {
                "success": True,
                "data": data,
                "message": f"Successfully read {count} coils from address {address}",
            }

        except ValueError as e:
            return {"success": False, "error": {"code": "VALIDATION_ERROR", "message": str(e)}}
        except Exception as e:
            logger.error(f"Error reading coils from server {server_id}: {e}")
            return {"success": False, "error": {"code": "READ_ERROR", "message": f"Failed to read coils: {str(e)}"}}

    def handle_server_write_coils(self, server_id: str, address: int, values: List[bool]) -> Dict[str, Any]:
        """Handle writing coils to a server's local datastore.

        Args:
            server_id: Server identifier
            address: Starting address
            values: List of boolean values to write

        Returns:
            Dictionary with success status and message or error information
        """
        try:
            validation = self._validate_write_params(server_id, address, values)
            if not validation["success"]:
                return validation

            server = self.server_manager.get_server(server_id)
            if not server:
                return self._server_not_found_error(server_id)

            server.write_coils(address, values)
            return {
                "success": True,
                "message": f"Successfully wrote {len(values)} coils to address {address}",
            }

        except ValueError as e:
            return {"success": False, "error": {"code": "VALIDATION_ERROR", "message": str(e)}}
        except Exception as e:
            logger.error(f"Error writing coils to server {server_id}: {e}")
            return {"success": False, "error": {"code": "WRITE_ERROR", "message": f"Failed to write coils: {str(e)}"}}

    def handle_server_read_discrete_inputs(self, server_id: str, address: int, count: int) -> Dict[str, Any]:
        """Handle reading discrete inputs from a server's local datastore.

        Args:
            server_id: Server identifier
            address: Starting address
            count: Number of discrete inputs to read

        Returns:
            Dictionary with success status and values or error information
        """
        try:
            validation = self._validate_read_params(server_id, address, count)
            if not validation["success"]:
                return validation

            server = self.server_manager.get_server(server_id)
            if not server:
                return self._server_not_found_error(server_id)

            data = server.read_discrete_inputs(address, count)
            return {
                "success": True,
                "data": data,
                "message": f"Successfully read {count} discrete inputs from address {address}",
            }

        except ValueError as e:
            return {"success": False, "error": {"code": "VALIDATION_ERROR", "message": str(e)}}
        except Exception as e:
            logger.error(f"Error reading discrete inputs from server {server_id}: {e}")
            return {"success": False, "error": {"code": "READ_ERROR", "message": f"Failed to read discrete inputs: {str(e)}"}}

    def handle_server_write_discrete_inputs(self, server_id: str, address: int, values: List[bool]) -> Dict[str, Any]:
        """Handle writing discrete inputs to a server's local datastore (server-side populate).

        Args:
            server_id: Server identifier
            address: Starting address
            values: List of boolean values to write

        Returns:
            Dictionary with success status and message or error information
        """
        try:
            validation = self._validate_write_params(server_id, address, values)
            if not validation["success"]:
                return validation

            server = self.server_manager.get_server(server_id)
            if not server:
                return self._server_not_found_error(server_id)

            server.write_discrete_inputs(address, values)
            return {
                "success": True,
                "message": f"Successfully wrote {len(values)} discrete inputs to address {address}",
            }

        except ValueError as e:
            return {"success": False, "error": {"code": "VALIDATION_ERROR", "message": str(e)}}
        except Exception as e:
            logger.error(f"Error writing discrete inputs to server {server_id}: {e}")
            return {"success": False, "error": {"code": "WRITE_ERROR", "message": f"Failed to write discrete inputs: {str(e)}"}}

    def handle_server_read_holding_registers(self, server_id: str, address: int, count: int) -> Dict[str, Any]:
        """Handle reading holding registers from a server's local datastore.

        Args:
            server_id: Server identifier
            address: Starting address
            count: Number of registers to read

        Returns:
            Dictionary with success status and register values or error information
        """
        try:
            validation = self._validate_read_params(server_id, address, count)
            if not validation["success"]:
                return validation

            server = self.server_manager.get_server(server_id)
            if not server:
                return self._server_not_found_error(server_id)

            data = server.read_holding_registers(address, count)
            return {
                "success": True,
                "data": data,
                "message": f"Successfully read {count} holding registers from address {address}",
            }

        except ValueError as e:
            return {"success": False, "error": {"code": "VALIDATION_ERROR", "message": str(e)}}
        except Exception as e:
            logger.error(f"Error reading holding registers from server {server_id}: {e}")
            return {"success": False, "error": {"code": "READ_ERROR", "message": f"Failed to read holding registers: {str(e)}"}}

    def handle_server_write_holding_registers(self, server_id: str, address: int, values: List[int]) -> Dict[str, Any]:
        """Handle writing holding registers to a server's local datastore.

        Args:
            server_id: Server identifier
            address: Starting address
            values: List of integer values to write

        Returns:
            Dictionary with success status and message or error information
        """
        try:
            validation = self._validate_write_params(server_id, address, values)
            if not validation["success"]:
                return validation

            server = self.server_manager.get_server(server_id)
            if not server:
                return self._server_not_found_error(server_id)

            server.write_holding_registers(address, values)
            return {
                "success": True,
                "message": f"Successfully wrote {len(values)} holding registers to address {address}",
            }

        except ValueError as e:
            return {"success": False, "error": {"code": "VALIDATION_ERROR", "message": str(e)}}
        except Exception as e:
            logger.error(f"Error writing holding registers to server {server_id}: {e}")
            return {"success": False, "error": {"code": "WRITE_ERROR", "message": f"Failed to write holding registers: {str(e)}"}}

    def handle_server_read_input_registers(self, server_id: str, address: int, count: int) -> Dict[str, Any]:
        """Handle reading input registers from a server's local datastore.

        Args:
            server_id: Server identifier
            address: Starting address
            count: Number of registers to read

        Returns:
            Dictionary with success status and register values or error information
        """
        try:
            validation = self._validate_read_params(server_id, address, count)
            if not validation["success"]:
                return validation

            server = self.server_manager.get_server(server_id)
            if not server:
                return self._server_not_found_error(server_id)

            data = server.read_input_registers(address, count)
            return {
                "success": True,
                "data": data,
                "message": f"Successfully read {count} input registers from address {address}",
            }

        except ValueError as e:
            return {"success": False, "error": {"code": "VALIDATION_ERROR", "message": str(e)}}
        except Exception as e:
            logger.error(f"Error reading input registers from server {server_id}: {e}")
            return {"success": False, "error": {"code": "READ_ERROR", "message": f"Failed to read input registers: {str(e)}"}}

    def handle_server_write_input_registers(self, server_id: str, address: int, values: List[int]) -> Dict[str, Any]:
        """Handle writing input registers to a server's local datastore (server-side populate).

        Args:
            server_id: Server identifier
            address: Starting address
            values: List of integer values to write

        Returns:
            Dictionary with success status and message or error information
        """
        try:
            validation = self._validate_write_params(server_id, address, values)
            if not validation["success"]:
                return validation

            server = self.server_manager.get_server(server_id)
            if not server:
                return self._server_not_found_error(server_id)

            server.write_input_registers(address, values)
            return {
                "success": True,
                "message": f"Successfully wrote {len(values)} input registers to address {address}",
            }

        except ValueError as e:
            return {"success": False, "error": {"code": "VALIDATION_ERROR", "message": str(e)}}
        except Exception as e:
            logger.error(f"Error writing input registers to server {server_id}: {e}")
            return {"success": False, "error": {"code": "WRITE_ERROR", "message": f"Failed to write input registers: {str(e)}"}}

    # ── Private helpers ────────────────────────────────────────────

    def _validate_read_params(self, server_id: str, address: int, count: int) -> Dict[str, Any]:
        """Validate common read operation parameters."""
        if not isinstance(server_id, str) or not server_id.strip():
            return self._validation_error("Server ID must be a non-empty string", "server_id", server_id)
        if not isinstance(address, int):
            return self._validation_error("Address must be an integer", "address", address)
        if not isinstance(count, int):
            return self._validation_error("Count must be an integer", "count", count)
        return {"success": True}

    def _validate_write_params(self, server_id: str, address: int, values: List[Union[bool, int]]) -> Dict[str, Any]:
        """Validate common write operation parameters."""
        if not isinstance(server_id, str) or not server_id.strip():
            return self._validation_error("Server ID must be a non-empty string", "server_id", server_id)
        if not isinstance(address, int):
            return self._validation_error("Address must be an integer", "address", address)
        if not isinstance(values, list):
            return self._validation_error("Values must be a list", "values", values)
        if not values:
            return self._validation_error("Values list cannot be empty", "values", values)
        return {"success": True}

    def _validation_error(self, message: str, parameter: str, value: Any) -> Dict[str, Any]:
        """Create a validation error response."""
        return {
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": message,
                "details": {"parameter": parameter, "provided_value": value},
            },
        }

    def _server_not_found_error(self, server_id: str) -> Dict[str, Any]:
        """Create a server not found error response."""
        return {
            "success": False,
            "error": {
                "code": "SERVER_NOT_FOUND",
                "message": f"Server with ID '{server_id}' not found",
            },
        }
