"""Validation utilities for Modbus operations."""

import ipaddress
import re
from typing import List


class ModbusValidator:
    """Validator for Modbus parameters and operations."""

    # Modbus protocol limits
    MAX_COILS_READ = 2000
    MAX_COILS_WRITE = 1968
    MAX_DISCRETE_INPUTS = 2000
    MAX_HOLDING_REGISTERS = 125
    MAX_INPUT_REGISTERS = 125
    MAX_HOLDING_REGISTERS_WRITE = 123

    @staticmethod
    def validate_slave_id(slave_id: int) -> None:
        """Validate slave ID is in valid range (1-247).
        
        Args:
            slave_id: The slave ID to validate
            
        Raises:
            ValueError: If slave ID is not in valid range
        """
        if not isinstance(slave_id, int):
            raise ValueError("Slave ID must be an integer")
        
        if not (1 <= slave_id <= 247):
            raise ValueError(f"Slave ID must be between 1 and 247, got {slave_id}")

    @staticmethod
    def validate_address_range(address: int, count: int, max_count: int, 
                             operation_name: str = "operation") -> None:
        """Validate address and count parameters.
        
        Args:
            address: Starting address
            count: Number of items to read/write
            max_count: Maximum allowed count for this operation
            operation_name: Name of the operation for error messages
            
        Raises:
            ValueError: If address or count is invalid
        """
        if not isinstance(address, int):
            raise ValueError("Address must be an integer")
        
        if not isinstance(count, int):
            raise ValueError("Count must be an integer")
        
        if address < 0:
            raise ValueError(f"Address must be non-negative, got {address}")
        
        if count <= 0:
            raise ValueError(f"Count must be positive, got {count}")
        
        if count > max_count:
            raise ValueError(
                f"{operation_name} count cannot exceed {max_count}, got {count}"
            )
        
        # Check for address overflow (Modbus addresses are 16-bit)
        if address + count > 65536:
            raise ValueError(
                f"Address range {address} to {address + count - 1} exceeds "
                f"maximum Modbus address space (0-65535)"
            )

    @staticmethod
    def validate_register_values(values: List[int]) -> None:
        """Validate register values are in 16-bit range (0-65535).
        
        Args:
            values: List of register values to validate
            
        Raises:
            ValueError: If any value is not in valid range
        """
        if not isinstance(values, list):
            raise ValueError("Values must be a list")
        
        if not values:
            raise ValueError("Values list cannot be empty")
        
        for i, value in enumerate(values):
            if not isinstance(value, int):
                raise ValueError(f"Value at index {i} must be an integer, got {type(value)}")
            
            if not (0 <= value <= 65535):
                raise ValueError(
                    f"Register value at index {i} must be between 0 and 65535, got {value}"
                )

    @staticmethod
    def validate_coil_values(values: List[bool]) -> None:
        """Validate coil values are boolean.
        
        Args:
            values: List of coil values to validate
            
        Raises:
            ValueError: If any value is not boolean
        """
        if not isinstance(values, list):
            raise ValueError("Values must be a list")
        
        if not values:
            raise ValueError("Values list cannot be empty")
        
        for i, value in enumerate(values):
            if not isinstance(value, bool):
                raise ValueError(f"Coil value at index {i} must be boolean, got {type(value)}")

    @staticmethod
    def validate_ip_address(host: str) -> None:
        """Validate IP address format.
        
        Args:
            host: IP address or hostname to validate
            
        Raises:
            ValueError: If IP address format is invalid
        """
        if not isinstance(host, str):
            raise ValueError("Host must be a string")
        
        if not host.strip():
            raise ValueError("Host cannot be empty")
        
        # Try to parse as IP address first
        try:
            ipaddress.ip_address(host)
            return
        except ValueError:
            pass
        
        # If not a valid IP, check if it's a valid hostname
        if not ModbusValidator._is_valid_hostname(host):
            raise ValueError(f"Invalid IP address or hostname: {host}")

    @staticmethod
    def validate_port(port: int) -> None:
        """Validate port number is in valid range (1-65535).
        
        Args:
            port: Port number to validate
            
        Raises:
            ValueError: If port is not in valid range
        """
        if not isinstance(port, int):
            raise ValueError("Port must be an integer")
        
        if not (1 <= port <= 65535):
            raise ValueError(f"Port must be between 1 and 65535, got {port}")

    @staticmethod
    def _is_valid_hostname(hostname: str) -> bool:
        """Check if hostname is valid according to RFC standards.
        
        Args:
            hostname: Hostname to validate
            
        Returns:
            True if hostname is valid, False otherwise
        """
        if len(hostname) > 253:
            return False
        
        # Remove trailing dot if present
        if hostname.endswith('.'):
            hostname = hostname[:-1]
        
        # Check each label
        labels = hostname.split('.')
        if not labels:
            return False
            
        for label in labels:
            if not label or len(label) > 63:
                return False
            
            # Label must start and end with alphanumeric
            if not re.match(r'^[a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?$', label):
                return False
        
        return True

    @classmethod
    def validate_coil_read_params(cls, address: int, count: int) -> None:
        """Validate parameters for coil read operation."""
        cls.validate_address_range(address, count, cls.MAX_COILS_READ, "Coil read")

    @classmethod
    def validate_coil_write_params(cls, address: int, values: List[bool]) -> None:
        """Validate parameters for coil write operation."""
        cls.validate_coil_values(values)
        count = len(values)
        cls.validate_address_range(address, count, cls.MAX_COILS_WRITE, "Coil write")

    @classmethod
    def validate_discrete_input_read_params(cls, address: int, count: int) -> None:
        """Validate parameters for discrete input read operation."""
        cls.validate_address_range(address, count, cls.MAX_DISCRETE_INPUTS, "Discrete input read")

    @classmethod
    def validate_holding_register_read_params(cls, address: int, count: int) -> None:
        """Validate parameters for holding register read operation."""
        cls.validate_address_range(address, count, cls.MAX_HOLDING_REGISTERS, "Holding register read")

    @classmethod
    def validate_holding_register_write_params(cls, address: int, values: List[int]) -> None:
        """Validate parameters for holding register write operation."""
        cls.validate_register_values(values)
        count = len(values)
        cls.validate_address_range(address, count, cls.MAX_HOLDING_REGISTERS_WRITE, "Holding register write")

    @classmethod
    def validate_input_register_read_params(cls, address: int, count: int) -> None:
        """Validate parameters for input register read operation."""
        cls.validate_address_range(address, count, cls.MAX_INPUT_REGISTERS, "Input register read")