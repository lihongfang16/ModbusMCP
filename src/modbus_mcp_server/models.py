"""Data models for the Modbus MCP Server."""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union


@dataclass
class SerialPortInfo:
    """Information about a serial port."""
    port: str
    description: str
    available: bool
    in_use_by_client: Optional[str] = None


@dataclass
class ClientInfo:
    """Information about a Modbus client connection."""
    client_id: str
    client_type: str  # "RTU" or "TCP"
    connection_params: Dict[str, Any]
    slave_id: int
    created_at: datetime
    last_used: datetime
    connected: bool


@dataclass
class ModbusResult:
    """Result of a Modbus operation."""
    success: bool
    data: Optional[List[Union[bool, int]]] = None
    error_message: Optional[str] = None
    error_code: Optional[str] = None


@dataclass
class RTUParams:
    """Parameters for RTU connection."""
    port: str
    baudrate: int
    bytesize: int = 8
    parity: str = 'N'
    stopbits: int = 1
    timeout: float = 3.0

    def __post_init__(self) -> None:
        """Validate RTU parameters after initialization."""
        if not isinstance(self.port, str) or not self.port.strip():
            raise ValueError("Port must be a non-empty string")
        
        valid_baudrates = [9600, 19200, 38400, 57600, 115200]
        if self.baudrate not in valid_baudrates:
            raise ValueError(f"Baudrate must be one of {valid_baudrates}")
        
        if self.bytesize not in [5, 6, 7, 8]:
            raise ValueError("Bytesize must be 5, 6, 7, or 8")
        
        if self.parity not in ['N', 'E', 'O', 'M', 'S']:
            raise ValueError("Parity must be 'N', 'E', 'O', 'M', or 'S'")
        
        if self.stopbits not in [1, 1.5, 2]:
            raise ValueError("Stopbits must be 1, 1.5, or 2")
        
        if self.timeout <= 0:
            raise ValueError("Timeout must be positive")


@dataclass
class ServerInfo:
    """Information about a running Modbus server."""
    server_id: str
    server_type: str  # "RTU" or "TCP"
    connection_params: Dict[str, Any]
    slave_id: int
    created_at: datetime
    running: bool


@dataclass
class ServerTCPParams:
    """Parameters for a Modbus TCP server."""
    host: str = "0.0.0.0"
    port: int = 502

    def __post_init__(self) -> None:
        """Validate TCP server parameters after initialization."""
        if not isinstance(self.host, str) or not self.host.strip():
            raise ValueError("Host must be a non-empty string")

        if not (1 <= self.port <= 65535):
            raise ValueError("Port must be between 1 and 65535")


@dataclass
class ServerRTUParams:
    """Parameters for a Modbus RTU server."""
    port: str
    baudrate: int
    bytesize: int = 8
    parity: str = 'N'
    stopbits: int = 1
    timeout: float = 3.0

    def __post_init__(self) -> None:
        """Validate RTU server parameters after initialization."""
        if not isinstance(self.port, str) or not self.port.strip():
            raise ValueError("Port must be a non-empty string")

        valid_baudrates = [9600, 19200, 38400, 57600, 115200]
        if self.baudrate not in valid_baudrates:
            raise ValueError(f"Baudrate must be one of {valid_baudrates}")

        if self.bytesize not in [5, 6, 7, 8]:
            raise ValueError("Bytesize must be 5, 6, 7, or 8")

        if self.parity not in ['N', 'E', 'O', 'M', 'S']:
            raise ValueError("Parity must be 'N', 'E', 'O', 'M', or 'S'")

        if self.stopbits not in [1, 1.5, 2]:
            raise ValueError("Stopbits must be 1, 1.5, or 2")

        if self.timeout <= 0:
            raise ValueError("Timeout must be positive")


@dataclass
class TCPParams:
    """Parameters for TCP connection."""
    host: str
    port: int = 502
    timeout: float = 3.0

    def __post_init__(self) -> None:
        """Validate TCP parameters after initialization."""
        if not isinstance(self.host, str) or not self.host.strip():
            raise ValueError("Host must be a non-empty string")
        
        if not (1 <= self.port <= 65535):
            raise ValueError("Port must be between 1 and 65535")
        
        if self.timeout <= 0:
            raise ValueError("Timeout must be positive")


class RegisterType(str, Enum):
    """Type of Modbus register."""
    coils = "coils"
    discrete_inputs = "discrete_inputs"
    holding_registers = "holding_registers"
    input_registers = "input_registers"


@dataclass
class LogEntry:
    """A log entry for a Modbus operation."""
    timestamp: str
    server_id: str
    register_type: RegisterType
    address: int
    operation: str  # "get" or "set"
    source: str  # "external" or "mcp"
    count: int
    alias: Optional[str] = None
    old_value: Optional[List[int]] = None
    new_value: Optional[List[int]] = None
    value: Optional[Any] = None
    success: bool = True
    message: Optional[str] = None


@dataclass
class AliasEntry:
    """An alias mapping for a Modbus register."""
    server_id: str
    register_type: RegisterType
    address: int
    alias: str