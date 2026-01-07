"""Connection manager for Modbus MCP Server."""

import logging
import threading
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Set

import serial.tools.list_ports
from pymodbus.exceptions import (
    ModbusException,
    ModbusIOException,
    ConnectionException,
    InvalidMessageReceivedException,
    MessageRegisterException,
    ParameterException,
    NotImplementedException
)

from .client_wrapper import ModbusClientWrapper
from .models import ClientInfo, RTUParams, SerialPortInfo, TCPParams
from .validation import ModbusValidator

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages Modbus client connections and resources."""
    
    def __init__(self):
        """Initialize the connection manager."""
        self.clients: Dict[str, ModbusClientWrapper] = {}
        self.client_info: Dict[str, ClientInfo] = {}
        self.used_ports: Set[str] = set()
        self._lock = threading.RLock()  # Reentrant lock for thread safety
        
        logger.info("ConnectionManager initialized")
    
    def list_serial_ports(self) -> List[SerialPortInfo]:
        """List available serial ports with availability status.
        
        Returns:
            List of SerialPortInfo objects with port details and availability
        """
        with self._lock:
            try:
                # Get all available serial ports
                ports = serial.tools.list_ports.comports()
                port_info_list = []
                
                for port in ports:
                    # Check if port is in use by an active RTU client
                    in_use_by = None
                    available = port.device not in self.used_ports
                    
                    if not available:
                        # Find which client is using this port
                        for client_id, info in self.client_info.items():
                            if (info.client_type == "RTU" and 
                                info.connection_params.get("port") == port.device):
                                in_use_by = client_id
                                break
                    
                    port_info = SerialPortInfo(
                        port=port.device,
                        description=port.description or "Unknown device",
                        available=available,
                        in_use_by_client=in_use_by
                    )
                    port_info_list.append(port_info)
                
                logger.debug(f"Listed {len(port_info_list)} serial ports")
                return port_info_list
                
            except Exception as e:
                logger.error(f"Error listing serial ports: {e}")
                return []
    
    def create_rtu_client(self, port: str, baudrate: int, slave_id: int) -> str:
        """Create RTU client and return unique ID.
        
        Args:
            port: Serial port name (e.g., 'COM1', '/dev/ttyUSB0')
            baudrate: Serial communication baud rate
            slave_id: Modbus slave ID
            
        Returns:
            Unique client identifier string
            
        Raises:
            ValueError: If parameters are invalid or port is already in use
        """
        with self._lock:
            # Validate parameters
            ModbusValidator.validate_slave_id(slave_id)
            
            # Check if port is already in use
            if port in self.used_ports:
                raise ValueError(f"Serial port {port} is already in use")
            
            # Create RTU parameters and validate them
            try:
                rtu_params = RTUParams(port=port, baudrate=baudrate)
            except ValueError as e:
                raise ValueError(f"Invalid RTU parameters: {e}")
            
            # Generate unique client ID
            client_id = self._generate_client_id()
            
            try:
                # Create the client wrapper
                client_wrapper = ModbusClientWrapper.create_rtu_client(rtu_params, slave_id)
                
                # Store client and metadata
                self.clients[client_id] = client_wrapper
                self.used_ports.add(port)
                
                # Create client info
                client_info = ClientInfo(
                    client_id=client_id,
                    client_type="RTU",
                    connection_params={
                        "port": port,
                        "baudrate": baudrate,
                        "bytesize": rtu_params.bytesize,
                        "parity": rtu_params.parity,
                        "stopbits": rtu_params.stopbits,
                        "timeout": rtu_params.timeout
                    },
                    slave_id=slave_id,
                    created_at=datetime.now(),
                    last_used=datetime.now(),
                    connected=False
                )
                self.client_info[client_id] = client_info
                
                logger.info(f"Created RTU client {client_id} for port {port}, slave {slave_id}")
                return client_id
                
            except ConnectionException as e:
                # Clean up on failure
                if client_id in self.clients:
                    del self.clients[client_id]
                if client_id in self.client_info:
                    del self.client_info[client_id]
                if port in self.used_ports:
                    self.used_ports.remove(port)
                
                logger.error(f"Connection error creating RTU client: {e}")
                raise ValueError(f"Failed to connect to RTU device on port {port}: {e}")
            except ModbusIOException as e:
                # Clean up on failure
                if client_id in self.clients:
                    del self.clients[client_id]
                if client_id in self.client_info:
                    del self.client_info[client_id]
                if port in self.used_ports:
                    self.used_ports.remove(port)
                
                logger.error(f"IO error creating RTU client: {e}")
                raise ValueError(f"IO error with RTU device on port {port}: {e}")
            except ModbusException as e:
                # Clean up on failure
                if client_id in self.clients:
                    del self.clients[client_id]
                if client_id in self.client_info:
                    del self.client_info[client_id]
                if port in self.used_ports:
                    self.used_ports.remove(port)
                
                logger.error(f"Modbus error creating RTU client: {e}")
                raise ValueError(f"Modbus protocol error with RTU device: {e}")
            except OSError as e:
                # Clean up on failure
                if client_id in self.clients:
                    del self.clients[client_id]
                if client_id in self.client_info:
                    del self.client_info[client_id]
                if port in self.used_ports:
                    self.used_ports.remove(port)
                
                logger.error(f"OS error creating RTU client: {e}")
                raise ValueError(f"System error accessing port {port}: {e}")
            except Exception as e:
                # Clean up on failure
                if client_id in self.clients:
                    del self.clients[client_id]
                if client_id in self.client_info:
                    del self.client_info[client_id]
                if port in self.used_ports:
                    self.used_ports.remove(port)
                
                logger.error(f"Failed to create RTU client: {e}")
                raise ValueError(f"Failed to create RTU client: {e}")
    
    def create_tcp_client(self, host: str, port: int = 502, slave_id: int = 1) -> str:
        """Create TCP client and return unique ID.
        
        Args:
            host: IP address or hostname of Modbus device
            port: TCP port number (default: 502)
            slave_id: Modbus slave ID (default: 1)
            
        Returns:
            Unique client identifier string
            
        Raises:
            ValueError: If parameters are invalid
        """
        with self._lock:
            # Validate parameters
            ModbusValidator.validate_slave_id(slave_id)
            
            # Create TCP parameters and validate them
            try:
                tcp_params = TCPParams(host=host, port=port)
            except ValueError as e:
                raise ValueError(f"Invalid TCP parameters: {e}")
            
            # Generate unique client ID
            client_id = self._generate_client_id()
            
            try:
                # Create the client wrapper
                client_wrapper = ModbusClientWrapper.create_tcp_client(tcp_params, slave_id)
                
                # Store client and metadata
                self.clients[client_id] = client_wrapper
                
                # Create client info
                client_info = ClientInfo(
                    client_id=client_id,
                    client_type="TCP",
                    connection_params={
                        "host": host,
                        "port": port,
                        "timeout": tcp_params.timeout
                    },
                    slave_id=slave_id,
                    created_at=datetime.now(),
                    last_used=datetime.now(),
                    connected=False
                )
                self.client_info[client_id] = client_info
                
                logger.info(f"Created TCP client {client_id} for {host}:{port}, slave {slave_id}")
                return client_id
                
            except ConnectionException as e:
                # Clean up on failure
                if client_id in self.clients:
                    del self.clients[client_id]
                if client_id in self.client_info:
                    del self.client_info[client_id]
                
                logger.error(f"Connection error creating TCP client: {e}")
                raise ValueError(f"Failed to connect to TCP device at {host}:{port}: {e}")
            except ModbusIOException as e:
                # Clean up on failure
                if client_id in self.clients:
                    del self.clients[client_id]
                if client_id in self.client_info:
                    del self.client_info[client_id]
                
                logger.error(f"IO error creating TCP client: {e}")
                raise ValueError(f"IO error with TCP device at {host}:{port}: {e}")
            except ModbusException as e:
                # Clean up on failure
                if client_id in self.clients:
                    del self.clients[client_id]
                if client_id in self.client_info:
                    del self.client_info[client_id]
                
                logger.error(f"Modbus error creating TCP client: {e}")
                raise ValueError(f"Modbus protocol error with TCP device: {e}")
            except OSError as e:
                # Clean up on failure
                if client_id in self.clients:
                    del self.clients[client_id]
                if client_id in self.client_info:
                    del self.client_info[client_id]
                
                logger.error(f"OS error creating TCP client: {e}")
                raise ValueError(f"Network error connecting to {host}:{port}: {e}")
            except Exception as e:
                # Clean up on failure
                if client_id in self.clients:
                    del self.clients[client_id]
                if client_id in self.client_info:
                    del self.client_info[client_id]
                
                logger.error(f"Failed to create TCP client: {e}")
                raise ValueError(f"Failed to create TCP client: {e}")
    
    def close_client(self, client_id: str) -> bool:
        """Close and remove client connection.
        
        Args:
            client_id: Unique identifier of the client to close
            
        Returns:
            True if client was successfully closed, False if client not found
        """
        with self._lock:
            if client_id not in self.clients:
                logger.warning(f"Attempted to close non-existent client: {client_id}")
                return False
            
            try:
                # Get client and info
                client = self.clients[client_id]
                info = self.client_info[client_id]
                
                # Disconnect the client
                client.disconnect()
                
                # Remove from used ports if RTU
                if info.client_type == "RTU":
                    port = info.connection_params.get("port")
                    if port and port in self.used_ports:
                        self.used_ports.remove(port)
                
                # Remove from storage
                del self.clients[client_id]
                del self.client_info[client_id]
                
                logger.info(f"Closed and removed client {client_id}")
                return True
                
            except Exception as e:
                logger.error(f"Error closing client {client_id}: {e}")
                # Still try to clean up storage
                try:
                    # Get info before cleanup for port removal
                    info = self.client_info.get(client_id)
                    
                    # Remove from used ports if RTU
                    if info and info.client_type == "RTU":
                        port = info.connection_params.get("port")
                        if port and port in self.used_ports:
                            self.used_ports.remove(port)
                    
                    # Remove from storage
                    if client_id in self.clients:
                        del self.clients[client_id]
                    if client_id in self.client_info:
                        del self.client_info[client_id]
                except Exception:
                    pass
                return False
    
    def get_client(self, client_id: str) -> Optional[ModbusClientWrapper]:
        """Retrieve client by ID.
        
        Args:
            client_id: Unique identifier of the client
            
        Returns:
            ModbusClientWrapper instance or None if not found
        """
        with self._lock:
            client = self.clients.get(client_id)
            if client and client_id in self.client_info:
                # Update last used timestamp
                self.client_info[client_id].last_used = datetime.now()
            return client
    
    def get_client_info(self, client_id: str) -> Optional[ClientInfo]:
        """Get client information by ID.
        
        Args:
            client_id: Unique identifier of the client
            
        Returns:
            ClientInfo instance or None if not found
        """
        with self._lock:
            return self.client_info.get(client_id)
    
    def list_clients(self) -> List[ClientInfo]:
        """List all active client connections.
        
        Returns:
            List of ClientInfo objects for all active clients
        """
        with self._lock:
            # Update connection status for all clients
            for client_id, client in self.clients.items():
                if client_id in self.client_info:
                    self.client_info[client_id].connected = client.is_connected()
            
            return list(self.client_info.values())
    
    def cleanup_all(self) -> None:
        """Close all client connections and clean up resources."""
        with self._lock:
            logger.info("Cleaning up all client connections")
            
            # Close all clients
            client_ids = list(self.clients.keys())
            for client_id in client_ids:
                try:
                    self.close_client(client_id)
                except Exception as e:
                    logger.error(f"Error during cleanup of client {client_id}: {e}")
            
            # Clear all data structures
            self.clients.clear()
            self.client_info.clear()
            self.used_ports.clear()
            
            logger.info("Cleanup completed")
    
    def _generate_client_id(self) -> str:
        """Generate a unique client identifier.
        
        Returns:
            Unique string identifier
        """
        # Generate UUID-based ID and ensure uniqueness
        while True:
            client_id = str(uuid.uuid4())
            if client_id not in self.clients:
                return client_id