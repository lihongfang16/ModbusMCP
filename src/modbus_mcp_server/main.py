"""Main entry point for the Modbus MCP Server."""

import asyncio
import logging
import signal
import sys
from typing import Any, Dict, List, Optional

from fastmcp import FastMCP

from .command_handlers import ModbusCommandHandlers
from .connection_manager import ConnectionManager
from .config import ServerConfig, load_config


def setup_logging(config: ServerConfig) -> None:
    """Set up logging configuration."""
    # Configure logging
    log_config = {
        'level': getattr(logging, config.log_level.upper()),
        'format': config.log_format,
    }
    
    # Add file handler if log file is specified
    if config.log_file:
        log_config['filename'] = config.log_file
        log_config['filemode'] = 'a'
    
    logging.basicConfig(**log_config)
    
    # Set up logger for this module
    logger = logging.getLogger(__name__)
    logger.info(f"Logging configured: level={config.log_level}, file={config.log_file}")


def create_app(config: ServerConfig) -> FastMCP:
    """Create and configure the FastMCP application."""
    app = FastMCP("modbus-server")
    
    # Initialize core components with configuration
    connection_manager = ConnectionManager()
    command_handlers = ModbusCommandHandlers(connection_manager)
    
    # Store references for cleanup and configuration
    app.connection_manager = connection_manager
    app.command_handlers = command_handlers
    app.config = config
    
    # Register MCP tools - will be implemented in subtask 7.2
    _register_tools(app, command_handlers)
    
    return app


def _register_tools(app: FastMCP, handlers: ModbusCommandHandlers) -> None:
    """Register all MCP tools with the FastMCP application.
    
    Args:
        app: FastMCP application instance
        handlers: Command handlers instance
    """
    
    @app.tool()
    def list_serial_ports() -> Dict[str, Any]:
        """List available serial ports on the system.
        
        Returns information about all detected serial ports including their
        availability status and which client (if any) is using them.
        
        Returns:
            Dictionary containing success status and list of serial port information
        """
        return handlers.handle_list_serial_ports()
    
    @app.tool()
    def create_rtu_client(port: str, baudrate: int, slave_id: int) -> Dict[str, Any]:
        """Create a Modbus RTU client connection.
        
        Creates a new RTU client for communicating with serial Modbus devices.
        
        Args:
            port: Serial port name (e.g., 'COM1' on Windows, '/dev/ttyUSB0' on Linux)
            baudrate: Serial communication baud rate (9600, 19200, 38400, 57600, 115200)
            slave_id: Modbus slave device ID (1-247)
            
        Returns:
            Dictionary containing success status and client ID or error information
        """
        return handlers.handle_create_rtu_client(port, baudrate, slave_id)
    
    @app.tool()
    def create_tcp_client(host: str, port: int = 502, slave_id: int = 1) -> Dict[str, Any]:
        """Create a Modbus TCP client connection.
        
        Creates a new TCP client for communicating with networked Modbus devices.
        
        Args:
            host: IP address or hostname of the Modbus device
            port: TCP port number (default: 502)
            slave_id: Modbus slave device ID (default: 1, range: 1-247)
            
        Returns:
            Dictionary containing success status and client ID or error information
        """
        return handlers.handle_create_tcp_client(host, port, slave_id)
    
    @app.tool()
    def close_client(client_id: str) -> Dict[str, Any]:
        """Close a Modbus client connection.
        
        Closes the specified client connection and releases all associated resources.
        
        Args:
            client_id: Unique identifier of the client to close
            
        Returns:
            Dictionary containing success status and message
        """
        return handlers.handle_close_client(client_id)
    
    @app.tool()
    def list_clients() -> Dict[str, Any]:
        """List all active Modbus client connections.
        
        Returns information about all currently active client connections
        including their type, connection parameters, and status.
        
        Returns:
            Dictionary containing success status and list of client information
        """
        return handlers.handle_list_clients()
    
    @app.tool()
    def read_coils(client_id: str, address: int, count: int) -> Dict[str, Any]:
        """Read coil values from a Modbus device.
        
        Reads the specified number of coils (digital outputs) starting from
        the given address. Coils are single-bit read/write registers.
        
        Args:
            client_id: Unique identifier of the client connection
            address: Starting coil address (0-based)
            count: Number of coils to read (1-2000)
            
        Returns:
            Dictionary containing success status and list of boolean values or error information
        """
        return handlers.handle_read_coils(client_id, address, count)
    
    @app.tool()
    def write_coils(client_id: str, address: int, values: List[bool]) -> Dict[str, Any]:
        """Write coil values to a Modbus device.
        
        Writes boolean values to coils (digital outputs) starting from
        the given address. Coils are single-bit read/write registers.
        
        Args:
            client_id: Unique identifier of the client connection
            address: Starting coil address (0-based)
            values: List of boolean values to write (max 1968 values)
            
        Returns:
            Dictionary containing success status and message or error information
        """
        return handlers.handle_write_coils(client_id, address, values)
    
    @app.tool()
    def read_discrete_inputs(client_id: str, address: int, count: int) -> Dict[str, Any]:
        """Read discrete input values from a Modbus device.
        
        Reads the specified number of discrete inputs (digital inputs) starting
        from the given address. Discrete inputs are single-bit read-only registers.
        
        Args:
            client_id: Unique identifier of the client connection
            address: Starting discrete input address (0-based)
            count: Number of discrete inputs to read (1-2000)
            
        Returns:
            Dictionary containing success status and list of boolean values or error information
        """
        return handlers.handle_read_discrete_inputs(client_id, address, count)
    
    @app.tool()
    def read_holding_registers(client_id: str, address: int, count: int) -> Dict[str, Any]:
        """Read holding register values from a Modbus device.
        
        Reads the specified number of holding registers (analog outputs/configuration)
        starting from the given address. Holding registers are 16-bit read/write registers.
        
        Args:
            client_id: Unique identifier of the client connection
            address: Starting holding register address (0-based)
            count: Number of holding registers to read (1-125)
            
        Returns:
            Dictionary containing success status and list of integer values or error information
        """
        return handlers.handle_read_holding_registers(client_id, address, count)
    
    @app.tool()
    def write_holding_registers(client_id: str, address: int, values: List[int]) -> Dict[str, Any]:
        """Write holding register values to a Modbus device.
        
        Writes integer values to holding registers (analog outputs/configuration)
        starting from the given address. Holding registers are 16-bit read/write registers.
        
        Args:
            client_id: Unique identifier of the client connection
            address: Starting holding register address (0-based)
            values: List of integer values to write (0-65535, max 123 values)
            
        Returns:
            Dictionary containing success status and message or error information
        """
        return handlers.handle_write_holding_registers(client_id, address, values)
    
    @app.tool()
    def read_input_registers(client_id: str, address: int, count: int) -> Dict[str, Any]:
        """Read input register values from a Modbus device.
        
        Reads the specified number of input registers (analog inputs/sensor data)
        starting from the given address. Input registers are 16-bit read-only registers.
        
        Args:
            client_id: Unique identifier of the client connection
            address: Starting input register address (0-based)
            count: Number of input registers to read (1-125)
            
        Returns:
            Dictionary containing success status and list of integer values or error information
        """
        return handlers.handle_read_input_registers(client_id, address, count)


async def main_async(config: ServerConfig) -> None:
    """Run the MCP server."""
    app = create_app(config)
    
    # Set up graceful shutdown
    def signal_handler(signum, frame):
        logging.info("Received shutdown signal, cleaning up...")
        if hasattr(app, 'connection_manager'):
            app.connection_manager.cleanup_all()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        logging.info(f"Modbus MCP Server starting with transport: {config.transport}")
        if config.transport == "stdio":
            await app.run(transport="stdio")
        else:
            logging.info(f"Server listening on {config.host}:{config.port}")
            await app.run(transport=config.transport, host=config.host, port=config.port)
    except Exception as e:
        logging.error(f"Server error: {e}")
        if hasattr(app, 'connection_manager'):
            app.connection_manager.cleanup_all()
        raise
    finally:
        # Cleanup on exit
        if hasattr(app, 'connection_manager'):
            app.connection_manager.cleanup_all()


def main(config_file: Optional[str] = None, config: Optional[ServerConfig] = None) -> None:
    """Main entry point."""
    try:
        # Load configuration
        if config is not None:
            server_config = config
        else:
            server_config = load_config(config_file)
        
        # Set up logging with configuration
        setup_logging(server_config)
        
        # Run the server
        asyncio.run(main_async(server_config))
    except KeyboardInterrupt:
        logging.info("Server stopped by user")
    except Exception as e:
        logging.error(f"Server failed to start: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()