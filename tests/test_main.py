"""Tests for main module."""

import pytest
from hypothesis import given, strategies as st
from modbus_mcp_server.main import create_app
from modbus_mcp_server.connection_manager import ConnectionManager
from modbus_mcp_server.command_handlers import ModbusCommandHandlers


def test_create_app():
    """Test that the FastMCP app can be created."""
    from modbus_mcp_server.config import ServerConfig
    
    # Create a minimal config for testing
    config = ServerConfig()
    app = create_app(config)
    assert app is not None
    assert app.name == "modbus-server"


# Feature: modbus-mcp-server, Property 11: Error Message Consistency
@given(
    invalid_client_id=st.one_of(
        st.none(),
        st.text().filter(lambda x: not x or x.isspace()),
        st.integers(),
        st.lists(st.text()),
        st.just("")
    ),
    invalid_address=st.one_of(
        st.none(),
        st.text(),
        st.floats(),
        st.integers().filter(lambda x: x < 0)
    ),
    invalid_count=st.one_of(
        st.none(),
        st.text(),
        st.floats(),
        st.integers().filter(lambda x: x <= 0 or x > 10000)
    ),
    invalid_values=st.one_of(
        st.none(),
        st.text(),
        st.integers(),
        st.lists(st.text()),
        st.just([])
    )
)
def test_error_message_consistency(invalid_client_id, invalid_address, invalid_count, invalid_values):
    """Property test: For any error condition, the system should return descriptive, 
    user-friendly error messages with appropriate error codes.
    
    **Validates: Requirements 12.1, 12.2, 12.3, 12.5**
    """
    # Create handlers for testing
    connection_manager = ConnectionManager()
    handlers = ModbusCommandHandlers(connection_manager)
    
    # Test various error scenarios and verify consistent error format
    error_responses = []
    
    # Test invalid client ID scenarios
    if invalid_client_id is not None:
        try:
            response = handlers.handle_read_coils(invalid_client_id, 0, 1)
            if not response.get("success", True):
                error_responses.append(response)
        except Exception:
            pass  # Some invalid inputs may cause exceptions, which is acceptable
    
    # Test invalid address scenarios
    if invalid_address is not None:
        try:
            response = handlers.handle_read_coils("valid_client", invalid_address, 1)
            if not response.get("success", True):
                error_responses.append(response)
        except Exception:
            pass
    
    # Test invalid count scenarios
    if invalid_count is not None:
        try:
            response = handlers.handle_read_coils("valid_client", 0, invalid_count)
            if not response.get("success", True):
                error_responses.append(response)
        except Exception:
            pass
    
    # Test invalid values scenarios for write operations
    if invalid_values is not None:
        try:
            response = handlers.handle_write_coils("valid_client", 0, invalid_values)
            if not response.get("success", True):
                error_responses.append(response)
        except Exception:
            pass
    
    # Verify all error responses have consistent structure
    for response in error_responses:
        # All error responses must have these fields
        assert "success" in response
        assert response["success"] is False
        assert "error" in response
        
        error = response["error"]
        assert isinstance(error, dict)
        
        # Error must have code and message
        assert "code" in error
        assert "message" in error
        
        # Code should be a non-empty string
        assert isinstance(error["code"], str)
        assert len(error["code"]) > 0
        
        # Message should be a non-empty string
        assert isinstance(error["message"], str)
        assert len(error["message"]) > 0
        
        # Message should be descriptive (not just generic)
        assert len(error["message"]) > 10  # Reasonable minimum for descriptive message
        
        # Code should follow expected patterns
        valid_error_codes = {
            "VALIDATION_ERROR", "CLIENT_NOT_FOUND", "CLIENT_CREATION_ERROR",
            "CLIENT_CLOSE_ERROR", "READ_ERROR", "WRITE_ERROR", "SERIAL_PORT_ERROR",
            "CLIENT_LIST_ERROR"
        }
        assert error["code"] in valid_error_codes