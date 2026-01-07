"""Tests for the ModbusCommandHandlers class."""

import pytest
from hypothesis import given, strategies as st, settings
from unittest.mock import Mock, patch

from modbus_mcp_server.command_handlers import ModbusCommandHandlers
from modbus_mcp_server.connection_manager import ConnectionManager


class TestModbusCommandHandlers:
    """Test cases for ModbusCommandHandlers."""
    
    def test_init(self):
        """Test ModbusCommandHandlers initialization."""
        cm = ConnectionManager()
        handlers = ModbusCommandHandlers(cm)
        assert handlers.connection_manager is cm
    
    @given(
        port=st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Pc'))),
        baudrate=st.sampled_from([9600, 19200, 38400, 57600, 115200]),
        slave_id=st.integers(min_value=1, max_value=247)
    )
    @settings(max_examples=100)
    def test_valid_rtu_parameter_acceptance_property(self, port, baudrate, slave_id):
        """Property test for valid RTU parameter acceptance.
        
        **Property 2: Valid Parameter Acceptance**
        **Validates: Requirements 1.1, 2.1**
        
        For any valid Modbus RTU connection parameters (valid port/baudrate/slave_id),
        client creation should succeed and return a valid client identifier.
        """
        # Feature: modbus-mcp-server, Property 2: Valid Parameter Acceptance
        cm = ConnectionManager()
        handlers = ModbusCommandHandlers(cm)
        
        # Mock successful client creation
        mock_client_id = "test-client-123"
        with patch.object(cm, 'create_rtu_client', return_value=mock_client_id) as mock_create:
            result = handlers.handle_create_rtu_client(port, baudrate, slave_id)
            
            # Property: Valid parameters should result in successful client creation
            assert result["success"] is True
            assert "client_id" in result
            assert result["client_id"] == mock_client_id
            assert "message" in result
            
            # Verify the connection manager was called with correct parameters
            mock_create.assert_called_once_with(port, baudrate, slave_id)
    
    @given(
        host=st.one_of(
            # Valid IP addresses
            st.builds(
                lambda a, b, c, d: f"{a}.{b}.{c}.{d}",
                st.integers(min_value=1, max_value=255),
                st.integers(min_value=0, max_value=255),
                st.integers(min_value=0, max_value=255),
                st.integers(min_value=1, max_value=254)
            ),
            # Valid hostnames
            st.text(
                min_size=1, 
                max_size=20, 
                alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))
            ).filter(lambda x: x and not x.startswith('-') and not x.endswith('-'))
        ),
        port=st.integers(min_value=1, max_value=65535),
        slave_id=st.integers(min_value=1, max_value=247)
    )
    @settings(max_examples=100)
    def test_valid_tcp_parameter_acceptance_property(self, host, port, slave_id):
        """Property test for valid TCP parameter acceptance.
        
        **Property 2: Valid Parameter Acceptance**
        **Validates: Requirements 1.1, 2.1**
        
        For any valid Modbus TCP connection parameters (valid host/port/slave_id),
        client creation should succeed and return a valid client identifier.
        """
        # Feature: modbus-mcp-server, Property 2: Valid Parameter Acceptance
        cm = ConnectionManager()
        handlers = ModbusCommandHandlers(cm)
        
        # Mock successful client creation
        mock_client_id = "test-tcp-client-456"
        with patch.object(cm, 'create_tcp_client', return_value=mock_client_id) as mock_create:
            result = handlers.handle_create_tcp_client(host, port, slave_id)
            
            # Property: Valid parameters should result in successful client creation
            assert result["success"] is True
            assert "client_id" in result
            assert result["client_id"] == mock_client_id
            assert "message" in result
            
            # Verify the connection manager was called with correct parameters
            mock_create.assert_called_once_with(host, port, slave_id)
    
    def test_handle_list_serial_ports_success(self):
        """Test successful serial port listing."""
        cm = ConnectionManager()
        handlers = ModbusCommandHandlers(cm)
        
        # Mock serial ports
        mock_ports = [
            Mock(port="COM1", description="Test Port 1", available=True, in_use_by_client=None),
            Mock(port="COM2", description="Test Port 2", available=False, in_use_by_client="client-123")
        ]
        
        with patch.object(cm, 'list_serial_ports', return_value=mock_ports):
            result = handlers.handle_list_serial_ports()
            
            assert result["success"] is True
            assert "ports" in result
            assert len(result["ports"]) == 2
            
            # Check first port
            port1 = result["ports"][0]
            assert port1["port"] == "COM1"
            assert port1["description"] == "Test Port 1"
            assert port1["available"] is True
            assert port1["in_use_by_client"] is None
            
            # Check second port
            port2 = result["ports"][1]
            assert port2["port"] == "COM2"
            assert port2["description"] == "Test Port 2"
            assert port2["available"] is False
            assert port2["in_use_by_client"] == "client-123"
    
    def test_handle_create_rtu_client_invalid_parameters(self):
        """Test RTU client creation with invalid parameters."""
        cm = ConnectionManager()
        handlers = ModbusCommandHandlers(cm)
        
        # Test empty port
        result = handlers.handle_create_rtu_client("", 9600, 1)
        assert result["success"] is False
        assert result["error"]["code"] == "VALIDATION_ERROR"
        assert "Port must be a non-empty string" in result["error"]["message"]
        
        # Test non-integer baudrate
        result = handlers.handle_create_rtu_client("COM1", "9600", 1)
        assert result["success"] is False
        assert result["error"]["code"] == "VALIDATION_ERROR"
        assert "Baudrate must be an integer" in result["error"]["message"]
        
        # Test non-integer slave_id
        result = handlers.handle_create_rtu_client("COM1", 9600, "1")
        assert result["success"] is False
        assert result["error"]["code"] == "VALIDATION_ERROR"
        assert "Slave ID must be an integer" in result["error"]["message"]
    
    def test_handle_create_tcp_client_invalid_parameters(self):
        """Test TCP client creation with invalid parameters."""
        cm = ConnectionManager()
        handlers = ModbusCommandHandlers(cm)
        
        # Test empty host
        result = handlers.handle_create_tcp_client("", 502, 1)
        assert result["success"] is False
        assert result["error"]["code"] == "VALIDATION_ERROR"
        assert "Host must be a non-empty string" in result["error"]["message"]
        
        # Test non-integer port
        result = handlers.handle_create_tcp_client("192.168.1.1", "502", 1)
        assert result["success"] is False
        assert result["error"]["code"] == "VALIDATION_ERROR"
        assert "Port must be an integer" in result["error"]["message"]
        
        # Test non-integer slave_id
        result = handlers.handle_create_tcp_client("192.168.1.1", 502, "1")
        assert result["success"] is False
        assert result["error"]["code"] == "VALIDATION_ERROR"
        assert "Slave ID must be an integer" in result["error"]["message"]
    
    def test_handle_create_rtu_client_connection_manager_error(self):
        """Test RTU client creation when connection manager raises an error."""
        cm = ConnectionManager()
        handlers = ModbusCommandHandlers(cm)
        
        # Mock connection manager to raise ValueError
        with patch.object(cm, 'create_rtu_client', side_effect=ValueError("Port already in use")):
            result = handlers.handle_create_rtu_client("COM1", 9600, 1)
            
            assert result["success"] is False
            assert result["error"]["code"] == "VALIDATION_ERROR"
            assert "Port already in use" in result["error"]["message"]
    
    def test_handle_create_tcp_client_connection_manager_error(self):
        """Test TCP client creation when connection manager raises an error."""
        cm = ConnectionManager()
        handlers = ModbusCommandHandlers(cm)
        
        # Mock connection manager to raise ValueError
        with patch.object(cm, 'create_tcp_client', side_effect=ValueError("Invalid host")):
            result = handlers.handle_create_tcp_client("invalid-host", 502, 1)
            
            assert result["success"] is False
            assert result["error"]["code"] == "VALIDATION_ERROR"
            assert "Invalid host" in result["error"]["message"]
    
    @given(
        client_id=st.one_of(
            # Invalid client IDs: empty strings, whitespace, non-existent UUIDs
            st.just(""),
            st.text(max_size=0),
            st.text().filter(lambda x: not x.strip()),
            st.uuids().map(str),  # Valid UUID format but non-existent
            st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Pc')))
        )
    )
    @settings(max_examples=100)
    def test_invalid_client_id_handling_property(self, client_id):
        """Property test for invalid client ID handling.
        
        **Property 5: Invalid Client ID Handling**
        **Validates: Requirements 3.2**
        
        For any non-existent or invalid client ID, all operations (close, read, write)
        should return appropriate error messages.
        """
        # Feature: modbus-mcp-server, Property 5: Invalid Client ID Handling
        cm = ConnectionManager()
        handlers = ModbusCommandHandlers(cm)
        
        # Mock connection manager to return None for any client ID (simulating non-existent client)
        with patch.object(cm, 'get_client', return_value=None):
            # Test close operation
            close_result = handlers.handle_close_client(client_id)
            
            # Property: Invalid client IDs should result in error responses
            if isinstance(client_id, str) and client_id.strip():
                # Valid string format but non-existent client
                assert close_result["success"] is False
                assert close_result["error"]["code"] == "CLIENT_NOT_FOUND"
                assert "not found" in close_result["error"]["message"].lower()
            else:
                # Invalid format (empty or whitespace)
                assert close_result["success"] is False
                assert close_result["error"]["code"] == "VALIDATION_ERROR"
                assert "non-empty string" in close_result["error"]["message"]
            
            # Test read operations with valid format client IDs
            if isinstance(client_id, str) and client_id.strip():
                # Test read coils
                read_result = handlers.handle_read_coils(client_id, 0, 1)
                assert read_result["success"] is False
                assert read_result["error"]["code"] == "CLIENT_NOT_FOUND"
                assert "not found" in read_result["error"]["message"].lower()
                
                # Test read discrete inputs
                discrete_result = handlers.handle_read_discrete_inputs(client_id, 0, 1)
                assert discrete_result["success"] is False
                assert discrete_result["error"]["code"] == "CLIENT_NOT_FOUND"
                assert "not found" in discrete_result["error"]["message"].lower()
                
                # Test read holding registers
                holding_result = handlers.handle_read_holding_registers(client_id, 0, 1)
                assert holding_result["success"] is False
                assert holding_result["error"]["code"] == "CLIENT_NOT_FOUND"
                assert "not found" in holding_result["error"]["message"].lower()
                
                # Test read input registers
                input_result = handlers.handle_read_input_registers(client_id, 0, 1)
                assert input_result["success"] is False
                assert input_result["error"]["code"] == "CLIENT_NOT_FOUND"
                assert "not found" in input_result["error"]["message"].lower()
                
                # Test write operations
                write_coils_result = handlers.handle_write_coils(client_id, 0, [True])
                assert write_coils_result["success"] is False
                assert write_coils_result["error"]["code"] == "CLIENT_NOT_FOUND"
                assert "not found" in write_coils_result["error"]["message"].lower()
                
                write_registers_result = handlers.handle_write_holding_registers(client_id, 0, [100])
                assert write_registers_result["success"] is False
                assert write_registers_result["error"]["code"] == "CLIENT_NOT_FOUND"
                assert "not found" in write_registers_result["error"]["message"].lower()
    
    def test_handle_close_client_invalid_client_id(self):
        """Test closing client with invalid client ID."""
        cm = ConnectionManager()
        handlers = ModbusCommandHandlers(cm)
        
        # Test with non-existent client ID
        result = handlers.handle_close_client("non-existent-client-123")
        assert result["success"] is False
        assert result["error"]["code"] == "CLIENT_NOT_FOUND"
        assert "not found" in result["error"]["message"]
    
    def test_read_operations_invalid_client_id(self):
        """Test read operations with invalid client ID."""
        cm = ConnectionManager()
        handlers = ModbusCommandHandlers(cm)
        
        # Test read coils with non-existent client
        result = handlers.handle_read_coils("non-existent-client", 0, 1)
        assert result["success"] is False
        assert result["error"]["code"] == "CLIENT_NOT_FOUND"
        assert "not found" in result["error"]["message"]
        
        # Test read discrete inputs with non-existent client
        result = handlers.handle_read_discrete_inputs("non-existent-client", 0, 1)
        assert result["success"] is False
        assert result["error"]["code"] == "CLIENT_NOT_FOUND"
        assert "not found" in result["error"]["message"]
        
        # Test read holding registers with non-existent client
        result = handlers.handle_read_holding_registers("non-existent-client", 0, 1)
        assert result["success"] is False
        assert result["error"]["code"] == "CLIENT_NOT_FOUND"
        assert "not found" in result["error"]["message"]
        
        # Test read input registers with non-existent client
        result = handlers.handle_read_input_registers("non-existent-client", 0, 1)
        assert result["success"] is False
        assert result["error"]["code"] == "CLIENT_NOT_FOUND"
        assert "not found" in result["error"]["message"]
    
    def test_write_operations_invalid_client_id(self):
        """Test write operations with invalid client ID."""
        cm = ConnectionManager()
        handlers = ModbusCommandHandlers(cm)
        
        # Test write coils with non-existent client
        result = handlers.handle_write_coils("non-existent-client", 0, [True, False])
        assert result["success"] is False
        assert result["error"]["code"] == "CLIENT_NOT_FOUND"
        assert "not found" in result["error"]["message"]
        
        # Test write holding registers with non-existent client
        result = handlers.handle_write_holding_registers("non-existent-client", 0, [100, 200])
        assert result["success"] is False
        assert result["error"]["code"] == "CLIENT_NOT_FOUND"
        assert "not found" in result["error"]["message"]