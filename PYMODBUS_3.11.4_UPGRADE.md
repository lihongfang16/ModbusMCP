# PyModbus 3.11.4 Upgrade Summary

## Changes Made

### 1. Dependency Updates
Updated the following files to use pymodbus 3.11.4:
- `pyproject.toml`: Changed `pymodbus>=3.6.0` to `pymodbus==3.11.4`
- `run_server.bat`: Updated pip install command to use `pymodbus==3.11.4`
- `run_server.ps1`: Updated pip install command to use `pymodbus==3.11.4`

### 2. Exception Handling Updates
Removed obsolete exception classes that were removed in pymodbus 3.11.4:

**Files Modified:**
- `src/modbus_mcp_server/client_wrapper.py`
- `src/modbus_mcp_server/connection_manager.py`

**Removed Exceptions:**
- `InvalidMessageReceivedException` - No longer exists in pymodbus 3.11.4
- `MessageRegisterException` - No longer exists in pymodbus 3.11.4

**Retained Exceptions:**
- `ModbusException` - Base exception class
- `ModbusIOException` - I/O and communication errors
- `ConnectionException` - Connection-related errors
- `ParameterException` - Invalid parameter errors
- `NotImplementedException` - Unsupported operations

### 3. API Compatibility
The code is fully compatible with pymodbus 3.11.4 because:
- The `slave=` parameter is still supported (backward compatible)
- All client methods remain unchanged:
  - `read_coils()`, `write_coil()`, `write_coils()`
  - `read_discrete_inputs()`
  - `read_holding_registers()`, `write_register()`, `write_registers()`
  - `read_input_registers()`
- Connection management APIs are stable
- The bit handling order was corrected in 3.11.0 (reverted from 3.10.0)

## Testing Instructions

### Prerequisites
Ensure you have a Modbus TCP server running at 127.0.0.1:5020

### Test Steps
1. Start the MCP server:
   ```bash
   .\run_server.bat
   ```

2. Enable the MCP server in your MCP client configuration

3. Test the following operations:
   - `list_serial_ports` - List available serial ports
   - `create_tcp_client` - Create TCP client connection to 127.0.0.1:5020
   - `read_holding_registers` - Read registers from the device
   - `write_holding_registers` - Write registers to the device
   - `read_coils` - Read coil values
   - `write_coils` - Write coil values
   - `read_discrete_inputs` - Read discrete inputs
   - `read_input_registers` - Read input registers
   - `list_clients` - List active connections
   - `close_client` - Close a client connection

## Key Changes in PyModbus 3.11.4

### From 3.11.0:
- Reverted wrong byte handling from v3.10.0
- Bit handling order is LSB→MSB for each byte
- Word ordering depends on big/little endian setting
- `readCoils` and other bit functions return bits in logical order (NOT byte order)

### From 3.10.0:
- `ModbusSlaveContext` replaced by `ModbusDeviceContext`
- `slave=`, `slaves=` replaced by `device_id=`, `device_ids=` (but `slave=` still works)
- Payload module removed (replaced by "convert_to/from_registers")

## Verification
✅ All imports successful
✅ Server starts without errors
✅ Exception handling updated
✅ Ready for testing with Modbus TCP server at 127.0.0.1:5020
