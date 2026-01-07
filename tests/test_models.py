"""Property-based tests for data models."""

import pytest
from hypothesis import given, strategies as st
from datetime import datetime
from typing import Dict, Any

from modbus_mcp_server.models import RTUParams, TCPParams, ClientInfo, ModbusResult, SerialPortInfo


class TestDataModelValidation:
    """Property-based tests for data model validation."""

    # Feature: modbus-mcp-server, Property 3: Invalid Parameter Rejection
    @given(
        port=st.one_of(
            st.just(""),  # Empty string
            st.just("   "),  # Whitespace only
            st.integers(),  # Non-string type
            st.none(),  # None value
        ),
        baudrate=st.integers().filter(lambda x: x not in [9600, 19200, 38400, 57600, 115200]),
        bytesize=st.integers().filter(lambda x: x not in [5, 6, 7, 8]),
        parity=st.text().filter(lambda x: x not in ['N', 'E', 'O', 'M', 'S']),
        stopbits=st.floats().filter(lambda x: x not in [1, 1.5, 2]),
        timeout=st.floats(max_value=0)  # Non-positive timeout
    )
    def test_rtu_params_invalid_parameter_rejection(self, port, baudrate, bytesize, parity, stopbits, timeout):
        """For any invalid RTU parameters, the system should reject them with descriptive errors.
        
        **Validates: Requirements 1.2, 2.2, 2.4, 1.5**
        """
        # Test invalid port
        if isinstance(port, str) and not port.strip():
            with pytest.raises(ValueError, match="Port must be a non-empty string"):
                RTUParams(port=port, baudrate=9600)
        elif not isinstance(port, str):
            with pytest.raises(ValueError, match="Port must be a non-empty string"):
                RTUParams(port=port, baudrate=9600)
        
        # Test invalid baudrate
        if isinstance(baudrate, int) and baudrate not in [9600, 19200, 38400, 57600, 115200]:
            with pytest.raises(ValueError, match="Baudrate must be one of"):
                RTUParams(port="COM1", baudrate=baudrate)
        
        # Test invalid bytesize
        if isinstance(bytesize, int) and bytesize not in [5, 6, 7, 8]:
            with pytest.raises(ValueError, match="Bytesize must be 5, 6, 7, or 8"):
                RTUParams(port="COM1", baudrate=9600, bytesize=bytesize)
        
        # Test invalid parity
        if isinstance(parity, str) and parity not in ['N', 'E', 'O', 'M', 'S']:
            with pytest.raises(ValueError, match="Parity must be"):
                RTUParams(port="COM1", baudrate=9600, parity=parity)
        
        # Test invalid stopbits
        if isinstance(stopbits, (int, float)) and stopbits not in [1, 1.5, 2]:
            with pytest.raises(ValueError, match="Stopbits must be 1, 1.5, or 2"):
                RTUParams(port="COM1", baudrate=9600, stopbits=stopbits)
        
        # Test invalid timeout
        if isinstance(timeout, (int, float)) and timeout <= 0:
            with pytest.raises(ValueError, match="Timeout must be positive"):
                RTUParams(port="COM1", baudrate=9600, timeout=timeout)

    @given(
        host=st.one_of(
            st.just(""),  # Empty string
            st.just("   "),  # Whitespace only
            st.integers(),  # Non-string type
            st.none(),  # None value
        ),
        port=st.integers().filter(lambda x: not (1 <= x <= 65535)),
        timeout=st.floats(max_value=0)  # Non-positive timeout
    )
    def test_tcp_params_invalid_parameter_rejection(self, host, port, timeout):
        """For any invalid TCP parameters, the system should reject them with descriptive errors.
        
        **Validates: Requirements 1.2, 2.2, 2.4, 1.5**
        """
        # Test invalid host
        if isinstance(host, str) and not host.strip():
            with pytest.raises(ValueError, match="Host must be a non-empty string"):
                TCPParams(host=host)
        elif not isinstance(host, str):
            with pytest.raises(ValueError, match="Host must be a non-empty string"):
                TCPParams(host=host)
        
        # Test invalid port
        if isinstance(port, int) and not (1 <= port <= 65535):
            with pytest.raises(ValueError, match="Port must be between 1 and 65535"):
                TCPParams(host="192.168.1.1", port=port)
        
        # Test invalid timeout
        if isinstance(timeout, (int, float)) and timeout <= 0:
            with pytest.raises(ValueError, match="Timeout must be positive"):
                TCPParams(host="192.168.1.1", timeout=timeout)

    @given(
        port=st.text(min_size=1).filter(lambda x: x.strip()),
        baudrate=st.sampled_from([9600, 19200, 38400, 57600, 115200]),
        bytesize=st.sampled_from([5, 6, 7, 8]),
        parity=st.sampled_from(['N', 'E', 'O', 'M', 'S']),
        stopbits=st.sampled_from([1, 1.5, 2]),
        timeout=st.floats(min_value=0.1, max_value=60.0)
    )
    def test_rtu_params_valid_parameter_acceptance(self, port, baudrate, bytesize, parity, stopbits, timeout):
        """For any valid RTU parameters, the system should accept them without errors.
        
        **Validates: Requirements 1.1, 2.1**
        """
        # Should not raise any exception
        params = RTUParams(
            port=port,
            baudrate=baudrate,
            bytesize=bytesize,
            parity=parity,
            stopbits=stopbits,
            timeout=timeout
        )
        
        assert params.port == port
        assert params.baudrate == baudrate
        assert params.bytesize == bytesize
        assert params.parity == parity
        assert params.stopbits == stopbits
        assert params.timeout == timeout

    @given(
        host=st.text(min_size=1).filter(lambda x: x.strip()),
        port=st.integers(min_value=1, max_value=65535),
        timeout=st.floats(min_value=0.1, max_value=60.0)
    )
    def test_tcp_params_valid_parameter_acceptance(self, host, port, timeout):
        """For any valid TCP parameters, the system should accept them without errors.
        
        **Validates: Requirements 1.1, 2.1**
        """
        # Should not raise any exception
        params = TCPParams(host=host, port=port, timeout=timeout)
        
        assert params.host == host
        assert params.port == port
        assert params.timeout == timeout


# Additional unit tests for specific examples and edge cases
class TestDataModelExamples:
    """Unit tests for specific examples and edge cases."""

    def test_rtu_params_default_values(self):
        """Test RTU parameters with default values."""
        params = RTUParams(port="COM1", baudrate=9600)
        
        assert params.port == "COM1"
        assert params.baudrate == 9600
        assert params.bytesize == 8
        assert params.parity == 'N'
        assert params.stopbits == 1
        assert params.timeout == 3.0

    def test_tcp_params_default_values(self):
        """Test TCP parameters with default values."""
        params = TCPParams(host="192.168.1.1")
        
        assert params.host == "192.168.1.1"
        assert params.port == 502
        assert params.timeout == 3.0

    def test_client_info_creation(self):
        """Test ClientInfo dataclass creation."""
        now = datetime.now()
        client_info = ClientInfo(
            client_id="test-client-1",
            client_type="RTU",
            connection_params={"port": "COM1", "baudrate": 9600},
            slave_id=1,
            created_at=now,
            last_used=now,
            connected=True
        )
        
        assert client_info.client_id == "test-client-1"
        assert client_info.client_type == "RTU"
        assert client_info.slave_id == 1
        assert client_info.connected is True

    def test_modbus_result_success(self):
        """Test ModbusResult for successful operation."""
        result = ModbusResult(success=True, data=[True, False, True])
        
        assert result.success is True
        assert result.data == [True, False, True]
        assert result.error_message is None
        assert result.error_code is None

    def test_modbus_result_error(self):
        """Test ModbusResult for error operation."""
        result = ModbusResult(
            success=False,
            error_message="Connection timeout",
            error_code="TIMEOUT_ERROR"
        )
        
        assert result.success is False
        assert result.data is None
        assert result.error_message == "Connection timeout"
        assert result.error_code == "TIMEOUT_ERROR"

    def test_serial_port_info(self):
        """Test SerialPortInfo dataclass."""
        port_info = SerialPortInfo(
            port="COM1",
            description="USB Serial Port",
            available=False,
            in_use_by_client="client-123"
        )
        
        assert port_info.port == "COM1"
        assert port_info.description == "USB Serial Port"
        assert port_info.available is False
        assert port_info.in_use_by_client == "client-123"