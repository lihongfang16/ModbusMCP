"""Modbus client wrapper providing unified interface for RTU and TCP clients."""

import logging
import time
from typing import List, Optional, Union

from pymodbus.client import ModbusSerialClient, ModbusTcpClient
from pymodbus.exceptions import (
    ModbusException,
    ModbusIOException,
    ConnectionException,
    ParameterException,
    NotImplementedException
)

from .models import ModbusResult, RTUParams, TCPParams
from .validation import ModbusValidator

logger = logging.getLogger(__name__)


class ModbusClientWrapper:
    """Wrapper around pymodbus clients with unified interface and error handling."""
    
    def __init__(self, client: Union[ModbusSerialClient, ModbusTcpClient], 
                 client_type: str, slave_id: int, max_retries: int = 3, retry_delay: float = 0.5):
        """Initialize the client wrapper.
        
        Args:
            client: The pymodbus client instance (RTU or TCP)
            client_type: Type of client ("RTU" or "TCP")
            slave_id: Modbus slave ID for this client
            max_retries: Maximum number of retry attempts for transient errors
            retry_delay: Delay between retry attempts in seconds
        """
        self.client = client
        self.client_type = client_type
        self.slave_id = slave_id
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.connected = False
        
        # Validate slave ID
        ModbusValidator.validate_slave_id(slave_id)
    
    def connect(self) -> bool:
        """Establish connection to Modbus device.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            if self.client.connect():
                self.connected = True
                logger.info(f"Connected to {self.client_type} client (slave {self.slave_id})")
                return True
            else:
                self.connected = False
                logger.warning(f"Failed to connect to {self.client_type} client (slave {self.slave_id})")
                return False
        except ConnectionException as e:
            self.connected = False
            logger.error(f"Connection error for {self.client_type} client: {e}")
            return False
        except ModbusIOException as e:
            self.connected = False
            logger.error(f"IO error during connection to {self.client_type} client: {e}")
            return False
        except ModbusException as e:
            self.connected = False
            logger.error(f"Modbus exception during connection to {self.client_type} client: {e}")
            return False
        except OSError as e:
            self.connected = False
            logger.error(f"OS error during connection to {self.client_type} client: {e}")
            return False
        except Exception as e:
            self.connected = False
            logger.error(f"Unexpected exception during connection to {self.client_type} client: {e}")
            return False
    
    def disconnect(self) -> None:
        """Close connection to Modbus device."""
        try:
            if hasattr(self.client, 'close'):
                self.client.close()
            self.connected = False
            logger.info(f"Disconnected from {self.client_type} client (slave {self.slave_id})")
        except ConnectionException as e:
            logger.error(f"Connection error during disconnection from {self.client_type} client: {e}")
            self.connected = False
        except ModbusIOException as e:
            logger.error(f"IO error during disconnection from {self.client_type} client: {e}")
            self.connected = False
        except ModbusException as e:
            logger.error(f"Modbus exception during disconnection from {self.client_type} client: {e}")
            self.connected = False
        except OSError as e:
            logger.error(f"OS error during disconnection from {self.client_type} client: {e}")
            self.connected = False
        except Exception as e:
            logger.error(f"Unexpected exception during disconnection from {self.client_type} client: {e}")
            self.connected = False
    
    def is_connected(self) -> bool:
        """Check if client is connected.
        
        Returns:
            True if connected, False otherwise
        """
        return self.connected and self.client.is_socket_open()
    
    def _is_transient_error(self, e: Exception) -> bool:
        """Check if an exception represents a transient error that should be retried.
        
        Args:
            e: The exception to check
            
        Returns:
            True if the error is transient and should be retried
        """
        # Transient errors that may resolve with retry
        transient_exceptions = (
            ConnectionException,
            ModbusIOException,
            OSError,
            TimeoutError
        )
        
        return isinstance(e, transient_exceptions)
    
    def _execute_with_retry(self, operation_name: str, operation_func, *args, **kwargs) -> ModbusResult:
        """Execute a Modbus operation with retry logic for transient errors.
        
        Args:
            operation_name: Name of the operation for logging
            operation_func: Function to execute
            *args: Arguments to pass to the operation function
            **kwargs: Keyword arguments to pass to the operation function
            
        Returns:
            ModbusResult with operation result or error information
        """
        last_exception = None
        
        for attempt in range(self.max_retries + 1):  # +1 for initial attempt
            try:
                return operation_func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                
                # If this is not a transient error, don't retry
                if not self._is_transient_error(e):
                    return self._handle_modbus_exception(operation_name, e)
                
                # If this is the last attempt, don't retry
                if attempt == self.max_retries:
                    logger.error(f"Operation {operation_name} failed after {self.max_retries + 1} attempts: {e}")
                    return self._handle_modbus_exception(operation_name, e)
                
                # Log retry attempt and wait before retrying
                logger.warning(f"Transient error in {operation_name} (attempt {attempt + 1}/{self.max_retries + 1}): {e}. Retrying in {self.retry_delay}s...")
                time.sleep(self.retry_delay)
        
        # This should never be reached, but just in case
        return self._handle_modbus_exception(operation_name, last_exception)

    def _handle_modbus_exception(self, operation: str, e: Exception) -> ModbusResult:
        """Convert pymodbus exceptions to user-friendly error messages.
        
        Args:
            operation: Description of the operation that failed
            e: The exception that occurred
            
        Returns:
            ModbusResult with appropriate error information
        """
        if isinstance(e, ConnectionException):
            return ModbusResult(
                success=False,
                error_message=f"Connection error during {operation}: {str(e)}",
                error_code="CONNECTION_ERROR"
            )
        elif isinstance(e, ModbusIOException):
            return ModbusResult(
                success=False,
                error_message=f"Communication error during {operation}: {str(e)}",
                error_code="COMMUNICATION_ERROR"
            )
        elif isinstance(e, ParameterException):
            return ModbusResult(
                success=False,
                error_message=f"Parameter error during {operation}: {str(e)}",
                error_code="PARAMETER_ERROR"
            )
        elif isinstance(e, NotImplementedException):
            return ModbusResult(
                success=False,
                error_message=f"Operation not supported during {operation}: {str(e)}",
                error_code="NOT_SUPPORTED"
            )
        elif isinstance(e, ModbusException):
            return ModbusResult(
                success=False,
                error_message=f"Modbus protocol error during {operation}: {str(e)}",
                error_code="MODBUS_PROTOCOL_ERROR"
            )
        elif isinstance(e, TimeoutError):
            return ModbusResult(
                success=False,
                error_message=f"Timeout error during {operation}: {str(e)}",
                error_code="TIMEOUT_ERROR"
            )
        elif isinstance(e, OSError):
            return ModbusResult(
                success=False,
                error_message=f"System error during {operation}: {str(e)}",
                error_code="SYSTEM_ERROR"
            )
        else:
            return ModbusResult(
                success=False,
                error_message=f"Unexpected error during {operation}: {str(e)}",
                error_code="UNEXPECTED_ERROR"
            )

    def _read_coils_operation(self, address: int, count: int) -> ModbusResult:
        """Internal method to perform coil reading operation without retry logic.
        
        Args:
            address: Starting address to read from
            count: Number of coils to read
            
        Returns:
            ModbusResult with coil values or error information
        """
        if not self.is_connected():
            return ModbusResult(
                success=False,
                error_message="Client is not connected",
                error_code="CONNECTION_ERROR"
            )
        
        # Perform the read operation
        response = self.client.read_coils(address, count=count, device_id=self.slave_id)
        
        if response.isError():
            return ModbusResult(
                success=False,
                error_message=f"Modbus error reading coils: {response}",
                error_code="MODBUS_ERROR"
            )
        
        # Convert response to boolean list
        coil_values = [bool(bit) for bit in response.bits[:count]]
        
        return ModbusResult(
            success=True,
            data=coil_values
        )

    def read_coils(self, address: int, count: int) -> ModbusResult:
        """Read coil values from the device.
        
        Args:
            address: Starting address to read from
            count: Number of coils to read
            
        Returns:
            ModbusResult with coil values as list of booleans or error information
        """
        try:
            # Validate parameters
            ModbusValidator.validate_coil_read_params(address, count)
            
            # Execute with retry logic
            return self._execute_with_retry("coil reading", self._read_coils_operation, address, count)
            
        except ValueError as e:
            return ModbusResult(
                success=False,
                error_message=f"Validation error: {str(e)}",
                error_code="VALIDATION_ERROR"
            )
        except Exception as e:
            return ModbusResult(
                success=False,
                error_message=f"Unexpected error reading coils: {str(e)}",
                error_code="UNEXPECTED_ERROR"
            )

    def _write_coils_operation(self, address: int, values: List[bool]) -> ModbusResult:
        """Internal method to perform coil writing operation without retry logic.
        
        Args:
            address: Starting address to write to
            values: List of boolean values to write
            
        Returns:
            ModbusResult indicating success or error information
        """
        if not self.is_connected():
            return ModbusResult(
                success=False,
                error_message="Client is not connected",
                error_code="CONNECTION_ERROR"
            )
        
        # Perform the write operation
        if len(values) == 1:
            # Single coil write
            response = self.client.write_coil(address, values[0], device_id=self.slave_id)
        else:
            # Multiple coil write
            response = self.client.write_coils(address, values, device_id=self.slave_id)
        
        if response.isError():
            return ModbusResult(
                success=False,
                error_message=f"Modbus error writing coils: {response}",
                error_code="MODBUS_ERROR"
            )
        
        return ModbusResult(success=True)

    def write_coils(self, address: int, values: List[bool]) -> ModbusResult:
        """Write coil values to the device.
        
        Args:
            address: Starting address to write to
            values: List of boolean values to write
            
        Returns:
            ModbusResult indicating success or error information
        """
        try:
            # Validate parameters
            ModbusValidator.validate_coil_write_params(address, values)
            
            # Execute with retry logic
            return self._execute_with_retry("coil writing", self._write_coils_operation, address, values)
            
        except ValueError as e:
            return ModbusResult(
                success=False,
                error_message=f"Validation error: {str(e)}",
                error_code="VALIDATION_ERROR"
            )
        except Exception as e:
            return ModbusResult(
                success=False,
                error_message=f"Unexpected error writing coils: {str(e)}",
                error_code="UNEXPECTED_ERROR"
            )

    def _read_discrete_inputs_operation(self, address: int, count: int) -> ModbusResult:
        """Internal method to perform discrete input reading operation without retry logic."""
        if not self.is_connected():
            return ModbusResult(
                success=False,
                error_message="Client is not connected",
                error_code="CONNECTION_ERROR"
            )
        
        response = self.client.read_discrete_inputs(address, count=count, device_id=self.slave_id)
        
        if response.isError():
            return ModbusResult(
                success=False,
                error_message=f"Modbus error reading discrete inputs: {response}",
                error_code="MODBUS_ERROR"
            )
        
        input_values = [bool(bit) for bit in response.bits[:count]]
        return ModbusResult(success=True, data=input_values)

    def read_discrete_inputs(self, address: int, count: int) -> ModbusResult:
        """Read discrete input values from the device.
        
        Args:
            address: Starting address to read from
            count: Number of discrete inputs to read
            
        Returns:
            ModbusResult with discrete input values as list of booleans or error information
        """
        try:
            # Validate parameters
            ModbusValidator.validate_discrete_input_read_params(address, count)
            
            # Execute with retry logic
            return self._execute_with_retry("discrete input reading", self._read_discrete_inputs_operation, address, count)
            
        except ValueError as e:
            return ModbusResult(
                success=False,
                error_message=f"Validation error: {str(e)}",
                error_code="VALIDATION_ERROR"
            )
        except Exception as e:
            return ModbusResult(
                success=False,
                error_message=f"Unexpected error reading discrete inputs: {str(e)}",
                error_code="UNEXPECTED_ERROR"
            )

    def _read_holding_registers_operation(self, address: int, count: int) -> ModbusResult:
        """Internal method to perform holding register reading operation without retry logic."""
        if not self.is_connected():
            return ModbusResult(
                success=False,
                error_message="Client is not connected",
                error_code="CONNECTION_ERROR"
            )
        
        response = self.client.read_holding_registers(address, count=count, device_id=self.slave_id)
        
        if response.isError():
            return ModbusResult(
                success=False,
                error_message=f"Modbus error reading holding registers: {response}",
                error_code="MODBUS_ERROR"
            )
        
        register_values = response.registers
        return ModbusResult(success=True, data=register_values)

    def read_holding_registers(self, address: int, count: int) -> ModbusResult:
        """Read holding register values from the device.
        
        Args:
            address: Starting address to read from
            count: Number of holding registers to read
            
        Returns:
            ModbusResult with register values as list of integers or error information
        """
        try:
            # Validate parameters
            ModbusValidator.validate_holding_register_read_params(address, count)
            
            # Execute with retry logic
            return self._execute_with_retry("holding register reading", self._read_holding_registers_operation, address, count)
            
        except ValueError as e:
            return ModbusResult(
                success=False,
                error_message=f"Validation error: {str(e)}",
                error_code="VALIDATION_ERROR"
            )
        except Exception as e:
            return ModbusResult(
                success=False,
                error_message=f"Unexpected error reading holding registers: {str(e)}",
                error_code="UNEXPECTED_ERROR"
            )

    def _write_holding_registers_operation(self, address: int, values: List[int]) -> ModbusResult:
        """Internal method to perform holding register writing operation without retry logic."""
        if not self.is_connected():
            return ModbusResult(
                success=False,
                error_message="Client is not connected",
                error_code="CONNECTION_ERROR"
            )
        
        if len(values) == 1:
            response = self.client.write_register(address, values[0], device_id=self.slave_id)
        else:
            response = self.client.write_registers(address, values, device_id=self.slave_id)
        
        if response.isError():
            return ModbusResult(
                success=False,
                error_message=f"Modbus error writing holding registers: {response}",
                error_code="MODBUS_ERROR"
            )
        
        return ModbusResult(success=True)

    def write_holding_registers(self, address: int, values: List[int]) -> ModbusResult:
        """Write holding register values to the device.
        
        Args:
            address: Starting address to write to
            values: List of integer values to write
            
        Returns:
            ModbusResult indicating success or error information
        """
        try:
            # Validate parameters
            ModbusValidator.validate_holding_register_write_params(address, values)
            
            # Execute with retry logic
            return self._execute_with_retry("holding register writing", self._write_holding_registers_operation, address, values)
            
        except ValueError as e:
            return ModbusResult(
                success=False,
                error_message=f"Validation error: {str(e)}",
                error_code="VALIDATION_ERROR"
            )
        except Exception as e:
            return ModbusResult(
                success=False,
                error_message=f"Unexpected error writing holding registers: {str(e)}",
                error_code="UNEXPECTED_ERROR"
            )

    def _read_input_registers_operation(self, address: int, count: int) -> ModbusResult:
        """Internal method to perform input register reading operation without retry logic."""
        if not self.is_connected():
            return ModbusResult(
                success=False,
                error_message="Client is not connected",
                error_code="CONNECTION_ERROR"
            )
        
        response = self.client.read_input_registers(address, count=count, device_id=self.slave_id)
        
        if response.isError():
            return ModbusResult(
                success=False,
                error_message=f"Modbus error reading input registers: {response}",
                error_code="MODBUS_ERROR"
            )
        
        register_values = response.registers
        return ModbusResult(success=True, data=register_values)

    def read_input_registers(self, address: int, count: int) -> ModbusResult:
        """Read input register values from the device.
        
        Args:
            address: Starting address to read from
            count: Number of input registers to read
            
        Returns:
            ModbusResult with register values as list of integers or error information
        """
        try:
            # Validate parameters
            ModbusValidator.validate_input_register_read_params(address, count)
            
            # Execute with retry logic
            return self._execute_with_retry("input register reading", self._read_input_registers_operation, address, count)
            
        except ValueError as e:
            return ModbusResult(
                success=False,
                error_message=f"Validation error: {str(e)}",
                error_code="VALIDATION_ERROR"
            )
        except Exception as e:
            return ModbusResult(
                success=False,
                error_message=f"Unexpected error reading input registers: {str(e)}",
                error_code="UNEXPECTED_ERROR"
            )

    @classmethod
    def create_rtu_client(cls, params: RTUParams, slave_id: int, max_retries: int = 3, retry_delay: float = 0.5) -> 'ModbusClientWrapper':
        """Create an RTU client wrapper.
        
        Args:
            params: RTU connection parameters
            slave_id: Modbus slave ID
            max_retries: Maximum number of retry attempts for transient errors
            retry_delay: Delay between retry attempts in seconds
            
        Returns:
            ModbusClientWrapper instance for RTU communication
        """
        client = ModbusSerialClient(
            port=params.port,
            baudrate=params.baudrate,
            bytesize=params.bytesize,
            parity=params.parity,
            stopbits=params.stopbits,
            timeout=params.timeout
        )
        
        return cls(client, "RTU", slave_id, max_retries, retry_delay)
    
    @classmethod
    def create_tcp_client(cls, params: TCPParams, slave_id: int, max_retries: int = 3, retry_delay: float = 0.5) -> 'ModbusClientWrapper':
        """Create a TCP client wrapper.
        
        Args:
            params: TCP connection parameters
            slave_id: Modbus slave ID
            max_retries: Maximum number of retry attempts for transient errors
            retry_delay: Delay between retry attempts in seconds
            
        Returns:
            ModbusClientWrapper instance for TCP communication
        """
        client = ModbusTcpClient(
            host=params.host,
            port=params.port,
            timeout=params.timeout
        )
        
        return cls(client, "TCP", slave_id, max_retries, retry_delay)