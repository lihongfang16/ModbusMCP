"""Property-based tests for validation utilities."""

import pytest
from hypothesis import given, strategies as st

from modbus_mcp_server.validation import ModbusValidator


class TestAddressRangeValidation:
    """Property-based tests for address range validation."""

    # Feature: modbus-mcp-server, Property 8: Address Range Validation
    @given(
        address=st.integers(min_value=0, max_value=65535),
        count=st.integers(min_value=1, max_value=2000),
        max_count=st.integers(min_value=1, max_value=2000)
    )
    def test_address_range_validation_valid_ranges(self, address, count, max_count):
        """For any valid address and count within limits, validation should pass.
        
        **Validates: Requirements 4.4, 6.4, 7.4, 9.4, 12.4**
        """
        # Only test cases where count is within max_count and address range is valid
        if count <= max_count and (address + count) <= 65536:
            # Should not raise any exception
            ModbusValidator.validate_address_range(address, count, max_count, "test operation")

    @given(
        address=st.one_of(
            st.integers(max_value=-1),  # Negative addresses
            st.floats(),  # Non-integer addresses
            st.text(),  # String addresses
            st.none()  # None addresses
        ),
        count=st.integers(min_value=1, max_value=100),
        max_count=st.integers(min_value=1, max_value=100)
    )
    def test_address_range_validation_invalid_addresses(self, address, count, max_count):
        """For any invalid address, validation should reject with descriptive errors.
        
        **Validates: Requirements 4.4, 6.4, 7.4, 9.4, 12.4**
        """
        if isinstance(address, int) and address < 0:
            with pytest.raises(ValueError, match="Address must be non-negative"):
                ModbusValidator.validate_address_range(address, count, max_count)
        elif not isinstance(address, int):
            with pytest.raises(ValueError, match="Address must be an integer"):
                ModbusValidator.validate_address_range(address, count, max_count)

    @given(
        address=st.integers(min_value=0, max_value=1000),
        count=st.one_of(
            st.integers(max_value=0),  # Non-positive counts
            st.floats(),  # Non-integer counts
            st.text(),  # String counts
            st.none()  # None counts
        ),
        max_count=st.integers(min_value=1, max_value=100)
    )
    def test_address_range_validation_invalid_counts(self, address, count, max_count):
        """For any invalid count, validation should reject with descriptive errors.
        
        **Validates: Requirements 4.4, 6.4, 7.4, 9.4, 12.4**
        """
        if isinstance(count, int) and count <= 0:
            with pytest.raises(ValueError, match="Count must be positive"):
                ModbusValidator.validate_address_range(address, count, max_count)
        elif not isinstance(count, int):
            with pytest.raises(ValueError, match="Count must be an integer"):
                ModbusValidator.validate_address_range(address, count, max_count)

    @given(
        address=st.integers(min_value=0, max_value=1000),
        count=st.integers(min_value=1, max_value=5000),
        max_count=st.integers(min_value=1, max_value=100)
    )
    def test_address_range_validation_count_exceeds_limit(self, address, count, max_count):
        """For any count exceeding the maximum allowed, validation should reject.
        
        **Validates: Requirements 4.4, 6.4, 7.4, 9.4, 12.4**
        """
        if count > max_count:
            with pytest.raises(ValueError, match=f"count cannot exceed {max_count}"):
                ModbusValidator.validate_address_range(address, count, max_count)

    @given(
        address=st.integers(min_value=65000, max_value=65535),
        count=st.integers(min_value=100, max_value=1000)
    )
    def test_address_range_validation_address_overflow(self, address, count):
        """For any address range that exceeds 16-bit space, validation should reject.
        
        **Validates: Requirements 4.4, 6.4, 7.4, 9.4, 12.4**
        """
        if (address + count) > 65536:
            with pytest.raises(ValueError, match="exceeds maximum Modbus address space"):
                ModbusValidator.validate_address_range(address, count, 2000)

    @given(
        slave_id=st.integers(min_value=1, max_value=247)
    )
    def test_slave_id_validation_valid_range(self, slave_id):
        """For any valid slave ID (1-247), validation should pass.
        
        **Validates: Requirements 1.5, 2.4**
        """
        # Should not raise any exception
        ModbusValidator.validate_slave_id(slave_id)

    @given(
        slave_id=st.one_of(
            st.integers(max_value=0),  # Too low
            st.integers(min_value=248),  # Too high
            st.floats(),  # Non-integer
            st.text(),  # String
            st.none()  # None
        )
    )
    def test_slave_id_validation_invalid_range(self, slave_id):
        """For any invalid slave ID, validation should reject with descriptive errors.
        
        **Validates: Requirements 1.5, 2.4**
        """
        if isinstance(slave_id, int) and not (1 <= slave_id <= 247):
            with pytest.raises(ValueError, match="Slave ID must be between 1 and 247"):
                ModbusValidator.validate_slave_id(slave_id)
        elif not isinstance(slave_id, int):
            with pytest.raises(ValueError, match="Slave ID must be an integer"):
                ModbusValidator.validate_slave_id(slave_id)

    @given(
        values=st.lists(st.integers(min_value=0, max_value=65535), min_size=1, max_size=100)
    )
    def test_register_values_validation_valid_range(self, values):
        """For any list of valid register values (0-65535), validation should pass.
        
        **Validates: Requirements 8.4**
        """
        # Should not raise any exception
        ModbusValidator.validate_register_values(values)

    @given(
        values=st.one_of(
            st.lists(st.integers().filter(lambda x: not (0 <= x <= 65535)), min_size=1),  # Out of range values
            st.lists(st.floats(), min_size=1),  # Non-integer values
            st.lists(st.text(), min_size=1),  # String values
            st.just([]),  # Empty list
            st.integers(),  # Not a list
            st.text(),  # String instead of list
            st.none()  # None
        )
    )
    def test_register_values_validation_invalid_values(self, values):
        """For any invalid register values, validation should reject with descriptive errors.
        
        **Validates: Requirements 8.4**
        """
        if isinstance(values, list):
            if not values:  # Empty list
                with pytest.raises(ValueError, match="Values list cannot be empty"):
                    ModbusValidator.validate_register_values(values)
            elif any(not isinstance(v, int) for v in values):  # Non-integer values
                with pytest.raises(ValueError, match="must be an integer"):
                    ModbusValidator.validate_register_values(values)
            elif any(not (0 <= v <= 65535) for v in values if isinstance(v, int)):  # Out of range
                with pytest.raises(ValueError, match="must be between 0 and 65535"):
                    ModbusValidator.validate_register_values(values)
        else:  # Not a list
            with pytest.raises(ValueError, match="Values must be a list"):
                ModbusValidator.validate_register_values(values)

    @given(
        values=st.lists(st.booleans(), min_size=1, max_size=100)
    )
    def test_coil_values_validation_valid_booleans(self, values):
        """For any list of boolean values, validation should pass.
        
        **Validates: Requirements 5.4**
        """
        # Should not raise any exception
        ModbusValidator.validate_coil_values(values)

    @given(
        values=st.one_of(
            st.lists(st.integers(), min_size=1),  # Integer values instead of booleans
            st.lists(st.text(), min_size=1),  # String values
            st.just([]),  # Empty list
            st.integers(),  # Not a list
            st.text(),  # String instead of list
            st.none()  # None
        )
    )
    def test_coil_values_validation_invalid_values(self, values):
        """For any invalid coil values, validation should reject with descriptive errors.
        
        **Validates: Requirements 5.4**
        """
        if isinstance(values, list):
            if not values:  # Empty list
                with pytest.raises(ValueError, match="Values list cannot be empty"):
                    ModbusValidator.validate_coil_values(values)
            elif any(not isinstance(v, bool) for v in values):  # Non-boolean values
                with pytest.raises(ValueError, match="must be boolean"):
                    ModbusValidator.validate_coil_values(values)
        else:  # Not a list
            with pytest.raises(ValueError, match="Values must be a list"):
                ModbusValidator.validate_coil_values(values)


# Additional unit tests for specific validation methods
class TestValidationExamples:
    """Unit tests for specific validation examples and edge cases."""

    def test_coil_read_params_validation(self):
        """Test coil read parameter validation."""
        # Valid case
        ModbusValidator.validate_coil_read_params(0, 100)
        
        # Invalid case - too many coils
        with pytest.raises(ValueError, match="Coil read count cannot exceed 2000"):
            ModbusValidator.validate_coil_read_params(0, 2001)

    def test_coil_write_params_validation(self):
        """Test coil write parameter validation."""
        # Valid case
        values = [True, False, True]
        ModbusValidator.validate_coil_write_params(0, values)
        
        # Invalid case - too many coils
        values = [True] * 1969
        with pytest.raises(ValueError, match="Coil write count cannot exceed 1968"):
            ModbusValidator.validate_coil_write_params(0, values)

    def test_holding_register_read_params_validation(self):
        """Test holding register read parameter validation."""
        # Valid case
        ModbusValidator.validate_holding_register_read_params(0, 100)
        
        # Invalid case - too many registers
        with pytest.raises(ValueError, match="Holding register read count cannot exceed 125"):
            ModbusValidator.validate_holding_register_read_params(0, 126)

    def test_holding_register_write_params_validation(self):
        """Test holding register write parameter validation."""
        # Valid case
        values = [100, 200, 300]
        ModbusValidator.validate_holding_register_write_params(0, values)
        
        # Invalid case - too many registers
        values = [100] * 124
        with pytest.raises(ValueError, match="Holding register write count cannot exceed 123"):
            ModbusValidator.validate_holding_register_write_params(0, values)

    def test_ip_address_validation(self):
        """Test IP address validation."""
        # Valid IP addresses
        ModbusValidator.validate_ip_address("192.168.1.1")
        ModbusValidator.validate_ip_address("10.0.0.1")
        ModbusValidator.validate_ip_address("127.0.0.1")
        
        # Valid hostnames
        ModbusValidator.validate_ip_address("localhost")
        ModbusValidator.validate_ip_address("example.com")
        
        # Invalid cases
        with pytest.raises(ValueError, match="Invalid IP address or hostname"):
            ModbusValidator.validate_ip_address("invalid..hostname")
        
        with pytest.raises(ValueError, match="Host cannot be empty"):
            ModbusValidator.validate_ip_address("")

    def test_port_validation(self):
        """Test port number validation."""
        # Valid ports
        ModbusValidator.validate_port(502)
        ModbusValidator.validate_port(1)
        ModbusValidator.validate_port(65535)
        
        # Invalid ports
        with pytest.raises(ValueError, match="Port must be between 1 and 65535"):
            ModbusValidator.validate_port(0)
        
        with pytest.raises(ValueError, match="Port must be between 1 and 65535"):
            ModbusValidator.validate_port(65536)
        
        with pytest.raises(ValueError, match="Port must be an integer"):
            ModbusValidator.validate_port("502")