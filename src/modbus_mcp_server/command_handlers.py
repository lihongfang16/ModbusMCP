"""Command handlers for Modbus MCP Server operations."""

import logging
from typing import Any, Dict, List, Union

from .connection_manager import ConnectionManager
from .models import ModbusResult
from .validation import ModbusValidator

logger = logging.getLogger(__name__)


class ModbusCommandHandlers:
    """Handles MCP tool commands for Modbus operations."""
    
    def __init__(self, connection_manager: ConnectionManager):
        """Initialize command handlers with connection manager.
        
        Args:
            connection_manager: ConnectionManager instance for client management
        """
        self.connection_manager = connection_manager
        logger.info("ModbusCommandHandlers initialized")
    
    def handle_list_serial_ports(self) -> Dict[str, Any]:
        """Handle listing available serial ports.
        
        Returns:
            Dictionary with success status and port information
        """
        try:
            ports = self.connection_manager.list_serial_ports()
            
            # Convert to serializable format
            port_data = []
            for port in ports:
                port_data.append({
                    "port": port.port,
                    "description": port.description,
                    "available": port.available,
                    "in_use_by_client": port.in_use_by_client
                })
            
            return {
                "success": True,
                "ports": port_data
            }
            
        except Exception as e:
            logger.error(f"Error listing serial ports: {e}")
            return {
                "success": False,
                "error": {
                    "code": "SERIAL_PORT_ERROR",
                    "message": f"Failed to list serial ports: {str(e)}"
                }
            }
    
    def handle_create_rtu_client(self, port: str, baudrate: int, slave_id: int) -> Dict[str, Any]:
        """Handle RTU client creation.
        
        Args:
            port: Serial port name
            baudrate: Serial communication baud rate
            slave_id: Modbus slave ID
            
        Returns:
            Dictionary with success status and client ID or error information
        """
        try:
            # Validate parameters
            if not isinstance(port, str) or not port.strip():
                return self._validation_error("Port must be a non-empty string", "port", port)
            
            if not isinstance(baudrate, int):
                return self._validation_error("Baudrate must be an integer", "baudrate", baudrate)
            
            if not isinstance(slave_id, int):
                return self._validation_error("Slave ID must be an integer", "slave_id", slave_id)
            
            # Create the client
            client_id = self.connection_manager.create_rtu_client(port, baudrate, slave_id)
            
            logger.info(f"Created RTU client {client_id} for port {port}")
            return {
                "success": True,
                "client_id": client_id,
                "message": f"RTU client created successfully for port {port}"
            }
            
        except ValueError as e:
            logger.warning(f"Validation error creating RTU client: {e}")
            return {
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": str(e)
                }
            }
        except Exception as e:
            logger.error(f"Error creating RTU client: {e}")
            return {
                "success": False,
                "error": {
                    "code": "CLIENT_CREATION_ERROR",
                    "message": f"Failed to create RTU client: {str(e)}"
                }
            }
    
    def handle_create_tcp_client(self, host: str, port: int = 502, slave_id: int = 1) -> Dict[str, Any]:
        """Handle TCP client creation.
        
        Args:
            host: IP address or hostname
            port: TCP port number (default: 502)
            slave_id: Modbus slave ID (default: 1)
            
        Returns:
            Dictionary with success status and client ID or error information
        """
        try:
            # Validate parameters
            if not isinstance(host, str) or not host.strip():
                return self._validation_error("Host must be a non-empty string", "host", host)
            
            if not isinstance(port, int):
                return self._validation_error("Port must be an integer", "port", port)
            
            if not isinstance(slave_id, int):
                return self._validation_error("Slave ID must be an integer", "slave_id", slave_id)
            
            # Create the client
            client_id = self.connection_manager.create_tcp_client(host, port, slave_id)
            
            logger.info(f"Created TCP client {client_id} for {host}:{port}")
            return {
                "success": True,
                "client_id": client_id,
                "message": f"TCP client created successfully for {host}:{port}"
            }
            
        except ValueError as e:
            logger.warning(f"Validation error creating TCP client: {e}")
            return {
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": str(e)
                }
            }
        except Exception as e:
            logger.error(f"Error creating TCP client: {e}")
            return {
                "success": False,
                "error": {
                    "code": "CLIENT_CREATION_ERROR",
                    "message": f"Failed to create TCP client: {str(e)}"
                }
            }
    
    def handle_close_client(self, client_id: str) -> Dict[str, Any]:
        """Handle client connection closure.
        
        Args:
            client_id: Unique identifier of the client to close
            
        Returns:
            Dictionary with success status and message
        """
        try:
            # Validate parameter
            if not isinstance(client_id, str) or not client_id.strip():
                return self._validation_error("Client ID must be a non-empty string", "client_id", client_id)
            
            # Check if client exists
            if not self.connection_manager.get_client(client_id):
                return {
                    "success": False,
                    "error": {
                        "code": "CLIENT_NOT_FOUND",
                        "message": f"Client with ID '{client_id}' not found"
                    }
                }
            
            # Close the client
            success = self.connection_manager.close_client(client_id)
            
            if success:
                logger.info(f"Closed client {client_id}")
                return {
                    "success": True,
                    "message": f"Client {client_id} closed successfully"
                }
            else:
                return {
                    "success": False,
                    "error": {
                        "code": "CLIENT_CLOSE_ERROR",
                        "message": f"Failed to close client {client_id}"
                    }
                }
                
        except Exception as e:
            logger.error(f"Error closing client {client_id}: {e}")
            return {
                "success": False,
                "error": {
                    "code": "CLIENT_CLOSE_ERROR",
                    "message": f"Failed to close client: {str(e)}"
                }
            }
    
    def handle_read_coils(self, client_id: str, address: int, count: int) -> Dict[str, Any]:
        """Handle coil reading operation.
        
        Args:
            client_id: Unique identifier of the client
            address: Starting address to read from
            count: Number of coils to read
            
        Returns:
            Dictionary with success status and coil values or error information
        """
        try:
            # Validate parameters
            validation_result = self._validate_read_params(client_id, address, count)
            if not validation_result["success"]:
                return validation_result
            
            # Additional validation for coils
            ModbusValidator.validate_coil_read_params(address, count)
            
            # Get client
            client = self.connection_manager.get_client(client_id)
            if not client:
                return self._client_not_found_error(client_id)
            
            # Perform read operation
            result = client.read_coils(address, count)
            
            if result.success:
                logger.debug(f"Read {count} coils from address {address} on client {client_id}")
                return {
                    "success": True,
                    "data": result.data,
                    "message": f"Successfully read {count} coils from address {address}"
                }
            else:
                return {
                    "success": False,
                    "error": {
                        "code": result.error_code or "READ_ERROR",
                        "message": result.error_message or "Failed to read coils"
                    }
                }
                
        except ValueError as e:
            logger.warning(f"Validation error reading coils: {e}")
            return {
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": str(e)
                }
            }
        except Exception as e:
            logger.error(f"Error reading coils: {e}")
            return {
                "success": False,
                "error": {
                    "code": "READ_ERROR",
                    "message": f"Failed to read coils: {str(e)}"
                }
            }
    
    def handle_write_coils(self, client_id: str, address: int, values: List[bool]) -> Dict[str, Any]:
        """Handle coil writing operation.
        
        Args:
            client_id: Unique identifier of the client
            address: Starting address to write to
            values: List of boolean values to write
            
        Returns:
            Dictionary with success status and message or error information
        """
        try:
            # Validate parameters
            validation_result = self._validate_write_params(client_id, address, values)
            if not validation_result["success"]:
                return validation_result
            
            # Additional validation for coils
            ModbusValidator.validate_coil_write_params(address, values)
            
            # Get client
            client = self.connection_manager.get_client(client_id)
            if not client:
                return self._client_not_found_error(client_id)
            
            # Perform write operation
            result = client.write_coils(address, values)
            
            if result.success:
                logger.debug(f"Wrote {len(values)} coils to address {address} on client {client_id}")
                return {
                    "success": True,
                    "message": f"Successfully wrote {len(values)} coils to address {address}"
                }
            else:
                return {
                    "success": False,
                    "error": {
                        "code": result.error_code or "WRITE_ERROR",
                        "message": result.error_message or "Failed to write coils"
                    }
                }
                
        except ValueError as e:
            logger.warning(f"Validation error writing coils: {e}")
            return {
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": str(e)
                }
            }
        except Exception as e:
            logger.error(f"Error writing coils: {e}")
            return {
                "success": False,
                "error": {
                    "code": "WRITE_ERROR",
                    "message": f"Failed to write coils: {str(e)}"
                }
            }
    
    def handle_read_discrete_inputs(self, client_id: str, address: int, count: int) -> Dict[str, Any]:
        """Handle discrete input reading operation.
        
        Args:
            client_id: Unique identifier of the client
            address: Starting address to read from
            count: Number of discrete inputs to read
            
        Returns:
            Dictionary with success status and input values or error information
        """
        try:
            # Validate parameters
            validation_result = self._validate_read_params(client_id, address, count)
            if not validation_result["success"]:
                return validation_result
            
            # Additional validation for discrete inputs
            ModbusValidator.validate_discrete_input_read_params(address, count)
            
            # Get client
            client = self.connection_manager.get_client(client_id)
            if not client:
                return self._client_not_found_error(client_id)
            
            # Perform read operation
            result = client.read_discrete_inputs(address, count)
            
            if result.success:
                logger.debug(f"Read {count} discrete inputs from address {address} on client {client_id}")
                return {
                    "success": True,
                    "data": result.data,
                    "message": f"Successfully read {count} discrete inputs from address {address}"
                }
            else:
                return {
                    "success": False,
                    "error": {
                        "code": result.error_code or "READ_ERROR",
                        "message": result.error_message or "Failed to read discrete inputs"
                    }
                }
                
        except ValueError as e:
            logger.warning(f"Validation error reading discrete inputs: {e}")
            return {
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": str(e)
                }
            }
        except Exception as e:
            logger.error(f"Error reading discrete inputs: {e}")
            return {
                "success": False,
                "error": {
                    "code": "READ_ERROR",
                    "message": f"Failed to read discrete inputs: {str(e)}"
                }
            }
    
    def handle_read_holding_registers(self, client_id: str, address: int, count: int) -> Dict[str, Any]:
        """Handle holding register reading operation.
        
        Args:
            client_id: Unique identifier of the client
            address: Starting address to read from
            count: Number of holding registers to read
            
        Returns:
            Dictionary with success status and register values or error information
        """
        try:
            # Validate parameters
            validation_result = self._validate_read_params(client_id, address, count)
            if not validation_result["success"]:
                return validation_result
            
            # Additional validation for holding registers
            ModbusValidator.validate_holding_register_read_params(address, count)
            
            # Get client
            client = self.connection_manager.get_client(client_id)
            if not client:
                return self._client_not_found_error(client_id)
            
            # Perform read operation
            result = client.read_holding_registers(address, count)
            
            if result.success:
                logger.debug(f"Read {count} holding registers from address {address} on client {client_id}")
                return {
                    "success": True,
                    "data": result.data,
                    "message": f"Successfully read {count} holding registers from address {address}"
                }
            else:
                return {
                    "success": False,
                    "error": {
                        "code": result.error_code or "READ_ERROR",
                        "message": result.error_message or "Failed to read holding registers"
                    }
                }
                
        except ValueError as e:
            logger.warning(f"Validation error reading holding registers: {e}")
            return {
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": str(e)
                }
            }
        except Exception as e:
            logger.error(f"Error reading holding registers: {e}")
            return {
                "success": False,
                "error": {
                    "code": "READ_ERROR",
                    "message": f"Failed to read holding registers: {str(e)}"
                }
            }
    
    def handle_write_holding_registers(self, client_id: str, address: int, values: List[int]) -> Dict[str, Any]:
        """Handle holding register writing operation.
        
        Args:
            client_id: Unique identifier of the client
            address: Starting address to write to
            values: List of integer values to write
            
        Returns:
            Dictionary with success status and message or error information
        """
        try:
            # Validate parameters
            validation_result = self._validate_write_params(client_id, address, values)
            if not validation_result["success"]:
                return validation_result
            
            # Additional validation for holding registers
            ModbusValidator.validate_holding_register_write_params(address, values)
            
            # Get client
            client = self.connection_manager.get_client(client_id)
            if not client:
                return self._client_not_found_error(client_id)
            
            # Perform write operation
            result = client.write_holding_registers(address, values)
            
            if result.success:
                logger.debug(f"Wrote {len(values)} holding registers to address {address} on client {client_id}")
                return {
                    "success": True,
                    "message": f"Successfully wrote {len(values)} holding registers to address {address}"
                }
            else:
                return {
                    "success": False,
                    "error": {
                        "code": result.error_code or "WRITE_ERROR",
                        "message": result.error_message or "Failed to write holding registers"
                    }
                }
                
        except ValueError as e:
            logger.warning(f"Validation error writing holding registers: {e}")
            return {
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": str(e)
                }
            }
        except Exception as e:
            logger.error(f"Error writing holding registers: {e}")
            return {
                "success": False,
                "error": {
                    "code": "WRITE_ERROR",
                    "message": f"Failed to write holding registers: {str(e)}"
                }
            }
    
    def handle_read_input_registers(self, client_id: str, address: int, count: int) -> Dict[str, Any]:
        """Handle input register reading operation.
        
        Args:
            client_id: Unique identifier of the client
            address: Starting address to read from
            count: Number of input registers to read
            
        Returns:
            Dictionary with success status and register values or error information
        """
        try:
            # Validate parameters
            validation_result = self._validate_read_params(client_id, address, count)
            if not validation_result["success"]:
                return validation_result
            
            # Additional validation for input registers
            ModbusValidator.validate_input_register_read_params(address, count)
            
            # Get client
            client = self.connection_manager.get_client(client_id)
            if not client:
                return self._client_not_found_error(client_id)
            
            # Perform read operation
            result = client.read_input_registers(address, count)
            
            if result.success:
                logger.debug(f"Read {count} input registers from address {address} on client {client_id}")
                return {
                    "success": True,
                    "data": result.data,
                    "message": f"Successfully read {count} input registers from address {address}"
                }
            else:
                return {
                    "success": False,
                    "error": {
                        "code": result.error_code or "READ_ERROR",
                        "message": result.error_message or "Failed to read input registers"
                    }
                }
                
        except ValueError as e:
            logger.warning(f"Validation error reading input registers: {e}")
            return {
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": str(e)
                }
            }
        except Exception as e:
            logger.error(f"Error reading input registers: {e}")
            return {
                "success": False,
                "error": {
                    "code": "READ_ERROR",
                    "message": f"Failed to read input registers: {str(e)}"
                }
            }
    
    def handle_list_clients(self) -> Dict[str, Any]:
        """Handle listing active client connections.
        
        Returns:
            Dictionary with success status and client information
        """
        try:
            clients = self.connection_manager.list_clients()
            
            # Convert to serializable format
            client_data = []
            for client in clients:
                client_data.append({
                    "client_id": client.client_id,
                    "client_type": client.client_type,
                    "connection_params": client.connection_params,
                    "slave_id": client.slave_id,
                    "created_at": client.created_at.isoformat(),
                    "last_used": client.last_used.isoformat(),
                    "connected": client.connected
                })
            
            return {
                "success": True,
                "clients": client_data
            }
            
        except Exception as e:
            logger.error(f"Error listing clients: {e}")
            return {
                "success": False,
                "error": {
                    "code": "CLIENT_LIST_ERROR",
                    "message": f"Failed to list clients: {str(e)}"
                }
            }
    
    def _validate_read_params(self, client_id: str, address: int, count: int) -> Dict[str, Any]:
        """Validate common read operation parameters.
        
        Args:
            client_id: Client identifier
            address: Starting address
            count: Number of items to read
            
        Returns:
            Dictionary with validation result
        """
        if not isinstance(client_id, str) or not client_id.strip():
            return self._validation_error("Client ID must be a non-empty string", "client_id", client_id)
        
        if not isinstance(address, int):
            return self._validation_error("Address must be an integer", "address", address)
        
        if not isinstance(count, int):
            return self._validation_error("Count must be an integer", "count", count)
        
        return {"success": True}
    
    def _validate_write_params(self, client_id: str, address: int, values: List[Union[bool, int]]) -> Dict[str, Any]:
        """Validate common write operation parameters.
        
        Args:
            client_id: Client identifier
            address: Starting address
            values: Values to write
            
        Returns:
            Dictionary with validation result
        """
        if not isinstance(client_id, str) or not client_id.strip():
            return self._validation_error("Client ID must be a non-empty string", "client_id", client_id)
        
        if not isinstance(address, int):
            return self._validation_error("Address must be an integer", "address", address)
        
        if not isinstance(values, list):
            return self._validation_error("Values must be a list", "values", values)
        
        if not values:
            return self._validation_error("Values list cannot be empty", "values", values)
        
        return {"success": True}
    
    def _validation_error(self, message: str, parameter: str, value: Any) -> Dict[str, Any]:
        """Create a validation error response.
        
        Args:
            message: Error message
            parameter: Parameter name that failed validation
            value: Invalid value
            
        Returns:
            Dictionary with validation error
        """
        return {
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": message,
                "details": {
                    "parameter": parameter,
                    "provided_value": value
                }
            }
        }
    
    def _client_not_found_error(self, client_id: str) -> Dict[str, Any]:
        """Create a client not found error response.
        
        Args:
            client_id: Client identifier that was not found
            
        Returns:
            Dictionary with client not found error
        """
        return {
            "success": False,
            "error": {
                "code": "CLIENT_NOT_FOUND",
                "message": f"Client with ID '{client_id}' not found"
            }
        }