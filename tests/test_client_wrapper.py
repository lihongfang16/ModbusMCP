"""Tests for ModbusClientWrapper class."""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock
from hypothesis import given, strategies as st

from pymodbus.exceptions import (
    ModbusException,
    ModbusIOException,
    ConnectionException,
    ParameterException,
    NotImplementedException
)

from src.modbus_mcp_server.client_wrapper import ModbusClientWrapper
from src.modbus_mcp_server.models import RTUParams, TCPParams, ModbusResult


class TestModbusClientWrapper:
    """Test cases for ModbusClientWrapper."""

    def test_create_rtu_client(self):
        """Test RTU client creation."""
        params = RTUParams(port="COM1", baudrate=9600)
        wrapper = ModbusClientWrapper.create_rtu_client(params, slave_id=1)
        
        assert wrapper.client_type == "RTU"
        assert wrapper.slave_id == 1
        assert not wrapper.connected

    def test_create_tcp_client(self):
        """Test TCP client creation."""
        params = TCPParams(host="192.168.1.100", port=502)
        wrapper = ModbusClientWrapper.create_tcp_client(params, slave_id=1)
        
        assert wrapper.client_type == "TCP"
        assert wrapper.slave_id == 1
        assert not wrapper.connected

    def test_invalid_slave_id_raises_error(self):
        """Test that invalid slave ID raises ValueError."""
        params = RTUParams(port="COM1", baudrate=9600)
        
        with pytest.raises(ValueError, match="Slave ID must be between 1 and 247"):
            ModbusClientWrapper.create_rtu_client(params, slave_id=0)
        
        with pytest.raises(ValueError, match="Slave ID must be between 1 and 247"):
            ModbusClientWrapper.create_rtu_client(params, slave_id=248)

    @patch('src.modbus_mcp_server.client_wrapper.ModbusSerialClient')
    def test_connect_success(self, mock_serial_client):
        """Test successful connection."""
        # Setup mock
        mock_client_instance = Mock()
        mock_client_instance.connect.return_value = True
        mock_serial_client.return_value = mock_client_instance
        
        params = RTUParams(port="COM1", baudrate=9600)
        wrapper = ModbusClientWrapper.create_rtu_client(params, slave_id=1)
        
        result = wrapper.connect()
        
        assert result is True
        assert wrapper.connected is True
        mock_client_instance.connect.assert_called_once()

    @patch('src.modbus_mcp_server.client_wrapper.ModbusSerialClient')
    def test_connect_failure(self, mock_serial_client):
        """Test failed connection."""
        # Setup mock
        mock_client_instance = Mock()
        mock_client_instance.connect.return_value = False
        mock_serial_client.return_value = mock_client_instance
        
        params = RTUParams(port="COM1", baudrate=9600)
        wrapper = ModbusClientWrapper.create_rtu_client(params, slave_id=1)
        
        result = wrapper.connect()
        
        assert result is False
        assert wrapper.connected is False

    @patch('src.modbus_mcp_server.client_wrapper.ModbusSerialClient')
    def test_disconnect(self, mock_serial_client):
        """Test disconnection."""
        # Setup mock
        mock_client_instance = Mock()
        mock_client_instance.connect.return_value = True
        mock_serial_client.return_value = mock_client_instance
        
        params = RTUParams(port="COM1", baudrate=9600)
        wrapper = ModbusClientWrapper.create_rtu_client(params, slave_id=1)
        
        # Connect first
        wrapper.connect()
        assert wrapper.connected is True
        
        # Then disconnect
        wrapper.disconnect()
        assert wrapper.connected is False
        mock_client_instance.close.assert_called_once()

    @given(
        client_type=st.sampled_from(["RTU", "TCP"]),
        slave_id=st.integers(min_value=1, max_value=247)
    )
    def test_property_client_lifecycle_management(self, client_type, slave_id):
        """
        Property 4: Client Lifecycle Management
        For any successfully created client, closing it with its client ID should succeed, 
        remove it from active connections, and prevent further operations on that ID.
        
        Feature: modbus-mcp-server, Property 4: Client Lifecycle Management
        Validates: Requirements 3.1, 3.3, 3.4
        """
        with patch('src.modbus_mcp_server.client_wrapper.ModbusSerialClient') as mock_serial, \
             patch('src.modbus_mcp_server.client_wrapper.ModbusTcpClient') as mock_tcp:
            
            # Setup mocks
            mock_client_instance = Mock()
            mock_client_instance.connect.return_value = True
            mock_client_instance.is_socket_open.return_value = True
            mock_serial.return_value = mock_client_instance
            mock_tcp.return_value = mock_client_instance
            
            # Create client based on type
            if client_type == "RTU":
                params = RTUParams(port="COM1", baudrate=9600)
                wrapper = ModbusClientWrapper.create_rtu_client(params, slave_id)
            else:  # TCP
                params = TCPParams(host="192.168.1.100", port=502)
                wrapper = ModbusClientWrapper.create_tcp_client(params, slave_id)
            
            # Test lifecycle: create -> connect -> disconnect
            
            # 1. Initially not connected
            assert not wrapper.connected
            assert not wrapper.is_connected()
            
            # 2. Connect should succeed
            connect_result = wrapper.connect()
            assert connect_result is True
            assert wrapper.connected is True
            assert wrapper.is_connected() is True
            
            # 3. Disconnect should succeed and change state
            wrapper.disconnect()
            assert wrapper.connected is False
            
            # 4. Operations on disconnected client should fail appropriately
            result = wrapper.read_coils(0, 1)
            assert not result.success
            assert result.error_code == "CONNECTION_ERROR"
            assert "not connected" in result.error_message.lower()
            
            # Verify mock calls
            mock_client_instance.connect.assert_called_once()
            mock_client_instance.close.assert_called_once()

    @given(
        operation_type=st.sampled_from(["coils", "discrete_inputs", "holding_registers", "input_registers"]),
        address=st.integers(min_value=0, max_value=1000),
        count=st.integers(min_value=1, max_value=10),
        slave_id=st.integers(min_value=1, max_value=247)
    )
    def test_property_read_operation_data_integrity(self, operation_type, address, count, slave_id):
        """
        Property 6: Read Operation Data Integrity
        For any valid read operation (coils, discrete inputs, holding registers, input registers), 
        successful operations should return data in the correct format (booleans for bits, integers for registers) 
        and failed operations should return descriptive errors.
        
        Feature: modbus-mcp-server, Property 6: Read Operation Data Integrity
        Validates: Requirements 4.2, 4.3, 6.2, 6.3, 7.2, 7.3, 9.2, 9.3
        """
        with patch('src.modbus_mcp_server.client_wrapper.ModbusSerialClient') as mock_serial:
            
            # Setup mock for successful response
            mock_client_instance = Mock()
            mock_client_instance.connect.return_value = True
            mock_client_instance.is_socket_open.return_value = True
            mock_serial.return_value = mock_client_instance
            
            # Create mock response based on operation type
            mock_response = Mock()
            mock_response.isError.return_value = False
            
            if operation_type in ["coils", "discrete_inputs"]:
                # For bit operations, return boolean data
                mock_response.bits = [True, False, True, False, True] * (count // 5 + 1)
                expected_data_type = bool
            else:
                # For register operations, return integer data
                mock_response.registers = list(range(count))
                expected_data_type = int
            
            # Setup the appropriate mock method
            if operation_type == "coils":
                mock_client_instance.read_coils.return_value = mock_response
            elif operation_type == "discrete_inputs":
                mock_client_instance.read_discrete_inputs.return_value = mock_response
            elif operation_type == "holding_registers":
                mock_client_instance.read_holding_registers.return_value = mock_response
            else:  # input_registers
                mock_client_instance.read_input_registers.return_value = mock_response
            
            # Create wrapper and connect
            params = RTUParams(port="COM1", baudrate=9600)
            wrapper = ModbusClientWrapper.create_rtu_client(params, slave_id)
            wrapper.connect()
            
            # Perform the read operation
            if operation_type == "coils":
                result = wrapper.read_coils(address, count)
            elif operation_type == "discrete_inputs":
                result = wrapper.read_discrete_inputs(address, count)
            elif operation_type == "holding_registers":
                result = wrapper.read_holding_registers(address, count)
            else:  # input_registers
                result = wrapper.read_input_registers(address, count)
            
            # Verify successful operation returns correct data format
            assert result.success is True
            assert result.data is not None
            assert len(result.data) == count
            
            # Verify data type is correct
            for item in result.data:
                assert isinstance(item, expected_data_type)
            
            # Test error case - mock a failed response
            mock_response.isError.return_value = True
            
            if operation_type == "coils":
                error_result = wrapper.read_coils(address, count)
            elif operation_type == "discrete_inputs":
                error_result = wrapper.read_discrete_inputs(address, count)
            elif operation_type == "holding_registers":
                error_result = wrapper.read_holding_registers(address, count)
            else:  # input_registers
                error_result = wrapper.read_input_registers(address, count)
            
            # Verify failed operation returns descriptive error
            assert error_result.success is False
            assert error_result.error_message is not None
            assert error_result.error_code == "MODBUS_ERROR"
            assert "Modbus error" in error_result.error_message

    @given(
        operation_type=st.sampled_from(["coils", "holding_registers"]),
        address=st.integers(min_value=0, max_value=1000),
        slave_id=st.integers(min_value=1, max_value=247)
    )
    def test_property_write_operation_validation(self, operation_type, address, slave_id):
        """
        Property 7: Write Operation Validation
        For any write operation (coils, holding registers), the system should validate that 
        the number of values matches the address range and that register values are within 
        16-bit range (0-65535).
        
        Feature: modbus-mcp-server, Property 7: Write Operation Validation
        Validates: Requirements 5.4, 8.4
        """
        with patch('src.modbus_mcp_server.client_wrapper.ModbusSerialClient') as mock_serial:
            
            # Setup mock for successful response
            mock_client_instance = Mock()
            mock_client_instance.connect.return_value = True
            mock_client_instance.is_socket_open.return_value = True
            mock_serial.return_value = mock_client_instance
            
            # Create mock response for successful write
            mock_response = Mock()
            mock_response.isError.return_value = False
            
            if operation_type == "coils":
                mock_client_instance.write_coil.return_value = mock_response
                mock_client_instance.write_coils.return_value = mock_response
            else:  # holding_registers
                mock_client_instance.write_register.return_value = mock_response
                mock_client_instance.write_registers.return_value = mock_response
            
            # Create wrapper and connect
            params = RTUParams(port="COM1", baudrate=9600)
            wrapper = ModbusClientWrapper.create_rtu_client(params, slave_id)
            wrapper.connect()
            
            # Test valid values
            if operation_type == "coils":
                # Test valid boolean values
                valid_values = [True, False, True]
                result = wrapper.write_coils(address, valid_values)
                assert result.success is True
                
                # Test invalid values (should be caught by validation)
                invalid_values = [1, 0, "true"]  # Non-boolean values
                result = wrapper.write_coils(address, invalid_values)
                assert result.success is False
                assert result.error_code == "VALIDATION_ERROR"
                
            else:  # holding_registers
                # Test valid register values (within 16-bit range)
                valid_values = [0, 32767, 65535]
                result = wrapper.write_holding_registers(address, valid_values)
                assert result.success is True
                
                # Test invalid register values (outside 16-bit range)
                invalid_values = [-1, 65536, 100000]
                result = wrapper.write_holding_registers(address, invalid_values)
                assert result.success is False
                assert result.error_code == "VALIDATION_ERROR"
                assert "must be between 0 and 65535" in result.error_message
            
            # Test empty values list (should fail validation)
            if operation_type == "coils":
                result = wrapper.write_coils(address, [])
            else:
                result = wrapper.write_holding_registers(address, [])
            
            assert result.success is False
            assert result.error_code == "VALIDATION_ERROR"
            assert "cannot be empty" in result.error_message


class TestErrorScenarios:
    """Test cases for error scenarios and exception handling."""

    @pytest.mark.parametrize("exception_class,expected_error_code", [
        (ConnectionException, "CONNECTION_ERROR"),
        (ModbusIOException, "COMMUNICATION_ERROR"),
        (ParameterException, "PARAMETER_ERROR"),
        (NotImplementedException, "NOT_SUPPORTED"),
        (ModbusException, "MODBUS_PROTOCOL_ERROR"),
        (OSError, "SYSTEM_ERROR"),
        (TimeoutError, "TIMEOUT_ERROR"),
    ])
    def test_pymodbus_exception_handling(self, exception_class, expected_error_code):
        """Test that pymodbus exceptions are properly converted to user-friendly error messages."""
        with patch('src.modbus_mcp_server.client_wrapper.ModbusSerialClient') as mock_serial:
            
            # Setup mock
            mock_client_instance = Mock()
            mock_client_instance.connect.return_value = True
            mock_client_instance.is_socket_open.return_value = True
            mock_serial.return_value = mock_client_instance
            
            # Make the read operation raise the specified exception
            mock_client_instance.read_coils.side_effect = exception_class("Test exception")
            
            # Create wrapper and connect
            params = RTUParams(port="COM1", baudrate=9600)
            wrapper = ModbusClientWrapper.create_rtu_client(params, slave_id=1)
            wrapper.connect()
            
            # Perform operation that should trigger exception
            result = wrapper.read_coils(0, 1)
            
            # Verify error handling
            assert result.success is False
            assert result.error_code == expected_error_code
            assert result.error_message is not None
            assert "Test exception" in result.error_message

    def test_connection_exception_handling(self):
        """Test handling of connection exceptions during connect/disconnect."""
        with patch('src.modbus_mcp_server.client_wrapper.ModbusSerialClient') as mock_serial:
            
            # Setup mock to raise ConnectionException on connect
            mock_client_instance = Mock()
            mock_client_instance.connect.side_effect = ConnectionException("Connection failed")
            mock_serial.return_value = mock_client_instance
            
            # Create wrapper
            params = RTUParams(port="COM1", baudrate=9600)
            wrapper = ModbusClientWrapper.create_rtu_client(params, slave_id=1)
            
            # Attempt to connect
            result = wrapper.connect()
            
            # Verify connection failure is handled gracefully
            assert result is False
            assert wrapper.connected is False

    def test_timeout_error_handling(self):
        """Test handling of timeout errors during operations."""
        with patch('src.modbus_mcp_server.client_wrapper.ModbusSerialClient') as mock_serial:
            
            # Setup mock
            mock_client_instance = Mock()
            mock_client_instance.connect.return_value = True
            mock_client_instance.is_socket_open.return_value = True
            mock_client_instance.read_coils.side_effect = TimeoutError("Operation timed out")
            mock_serial.return_value = mock_client_instance
            
            # Create wrapper and connect
            params = RTUParams(port="COM1", baudrate=9600, timeout=1.0)
            wrapper = ModbusClientWrapper.create_rtu_client(params, slave_id=1)
            wrapper.connect()
            
            # Perform operation that should timeout
            result = wrapper.read_coils(0, 1)
            
            # Verify timeout is handled properly
            assert result.success is False
            assert result.error_code == "TIMEOUT_ERROR"
            assert "timeout" in result.error_message.lower()

    def test_retry_logic_for_transient_errors(self):
        """Test that transient errors trigger retry logic."""
        with patch('src.modbus_mcp_server.client_wrapper.ModbusSerialClient') as mock_serial, \
             patch('time.sleep') as mock_sleep:  # Mock sleep to speed up test
            
            # Setup mock
            mock_client_instance = Mock()
            mock_client_instance.connect.return_value = True
            mock_client_instance.is_socket_open.return_value = True
            mock_serial.return_value = mock_client_instance
            
            # Make the first two calls fail with transient error, third succeeds
            mock_response = Mock()
            mock_response.isError.return_value = False
            mock_response.bits = [True, False]
            
            mock_client_instance.read_coils.side_effect = [
                ConnectionException("Transient connection error"),
                ModbusIOException("Transient IO error"),
                mock_response  # Success on third attempt
            ]
            
            # Create wrapper with retry settings
            params = RTUParams(port="COM1", baudrate=9600)
            wrapper = ModbusClientWrapper.create_rtu_client(params, slave_id=1, max_retries=3, retry_delay=0.1)
            wrapper.connect()
            
            # Perform operation
            result = wrapper.read_coils(0, 2)
            
            # Verify operation eventually succeeded after retries
            assert result.success is True
            assert result.data == [True, False]
            
            # Verify retry attempts were made
            assert mock_client_instance.read_coils.call_count == 3
            assert mock_sleep.call_count == 2  # Two retry delays

    def test_retry_logic_exhaustion(self):
        """Test that retry logic eventually gives up after max attempts."""
        with patch('src.modbus_mcp_server.client_wrapper.ModbusSerialClient') as mock_serial, \
             patch('time.sleep') as mock_sleep:
            
            # Setup mock
            mock_client_instance = Mock()
            mock_client_instance.connect.return_value = True
            mock_client_instance.is_socket_open.return_value = True
            mock_serial.return_value = mock_client_instance
            
            # Make all calls fail with transient error
            mock_client_instance.read_coils.side_effect = ConnectionException("Persistent connection error")
            
            # Create wrapper with limited retries
            params = RTUParams(port="COM1", baudrate=9600)
            wrapper = ModbusClientWrapper.create_rtu_client(params, slave_id=1, max_retries=2, retry_delay=0.1)
            wrapper.connect()
            
            # Perform operation
            result = wrapper.read_coils(0, 1)
            
            # Verify operation failed after exhausting retries
            assert result.success is False
            assert result.error_code == "CONNECTION_ERROR"
            assert "Persistent connection error" in result.error_message
            
            # Verify correct number of attempts (initial + retries)
            assert mock_client_instance.read_coils.call_count == 3  # 1 initial + 2 retries
            assert mock_sleep.call_count == 2  # Two retry delays

    def test_non_transient_errors_no_retry(self):
        """Test that non-transient errors don't trigger retry logic."""
        with patch('src.modbus_mcp_server.client_wrapper.ModbusSerialClient') as mock_serial, \
             patch('time.sleep') as mock_sleep:
            
            # Setup mock
            mock_client_instance = Mock()
            mock_client_instance.connect.return_value = True
            mock_client_instance.is_socket_open.return_value = True
            mock_serial.return_value = mock_client_instance
            
            # Make call fail with non-transient error
            mock_client_instance.read_coils.side_effect = ParameterException("Invalid parameter")
            
            # Create wrapper
            params = RTUParams(port="COM1", baudrate=9600)
            wrapper = ModbusClientWrapper.create_rtu_client(params, slave_id=1, max_retries=3)
            wrapper.connect()
            
            # Perform operation
            result = wrapper.read_coils(0, 1)
            
            # Verify operation failed immediately without retries
            assert result.success is False
            assert result.error_code == "PARAMETER_ERROR"
            assert "Invalid parameter" in result.error_message
            
            # Verify no retries were attempted
            assert mock_client_instance.read_coils.call_count == 1
            assert mock_sleep.call_count == 0

    def test_communication_failure_scenarios(self):
        """Test various communication failure scenarios."""
        with patch('src.modbus_mcp_server.client_wrapper.ModbusSerialClient') as mock_serial:
            
            # Setup mock
            mock_client_instance = Mock()
            mock_client_instance.connect.return_value = True
            mock_client_instance.is_socket_open.return_value = True
            mock_serial.return_value = mock_client_instance
            
            # Create wrapper
            params = RTUParams(port="COM1", baudrate=9600)
            wrapper = ModbusClientWrapper.create_rtu_client(params, slave_id=1)
            wrapper.connect()
            
            # Test different communication failures
            test_cases = [
                (ModbusIOException("Device not responding"), "COMMUNICATION_ERROR"),
                (OSError("Serial port error"), "SYSTEM_ERROR"),
            ]
            
            for exception, expected_code in test_cases:
                mock_client_instance.read_coils.side_effect = exception
                
                result = wrapper.read_coils(0, 1)
                
                assert result.success is False
                assert result.error_code == expected_code
                assert result.error_message is not None

    def test_validation_error_scenarios(self):
        """Test validation error scenarios."""
        params = RTUParams(port="COM1", baudrate=9600)
        wrapper = ModbusClientWrapper.create_rtu_client(params, slave_id=1)
        
        # Test invalid address ranges
        result = wrapper.read_coils(-1, 1)  # Negative address
        assert result.success is False
        assert result.error_code == "VALIDATION_ERROR"
        
        result = wrapper.read_coils(0, 0)  # Zero count
        assert result.success is False
        assert result.error_code == "VALIDATION_ERROR"
        
        result = wrapper.read_coils(0, 3000)  # Excessive count for coils
        assert result.success is False
        assert result.error_code == "VALIDATION_ERROR"

    def test_disconnected_client_operations(self):
        """Test that operations on disconnected clients return appropriate errors."""
        params = RTUParams(port="COM1", baudrate=9600)
        wrapper = ModbusClientWrapper.create_rtu_client(params, slave_id=1)
        
        # Don't connect the client
        
        # All operations should fail with connection error
        operations = [
            lambda: wrapper.read_coils(0, 1),
            lambda: wrapper.write_coils(0, [True]),
            lambda: wrapper.read_discrete_inputs(0, 1),
            lambda: wrapper.read_holding_registers(0, 1),
            lambda: wrapper.write_holding_registers(0, [100]),
            lambda: wrapper.read_input_registers(0, 1),
        ]
        
        for operation in operations:
            result = operation()
            assert result.success is False
            assert result.error_code == "CONNECTION_ERROR"
            assert "not connected" in result.error_message.lower()