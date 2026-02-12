# Modbus MCP Server

An MCP (Model Context Protocol) server that provides Modbus client and server (slave) functionality, enabling LLM applications to interact with Modbus RTU and TCP devices through a standardized interface. This server acts as a bridge between AI assistants and industrial automation systems, PLCs, sensors, and other Modbus-enabled devices.

## Features

- **Modbus RTU and TCP client support** - Connect to serial and network Modbus devices
- **Modbus RTU and TCP server (slave) support** - Run simulated Modbus devices that respond to client requests
- **Serial port discovery and management** - Automatically detect available serial ports
- **Comprehensive read/write operations** - Support for coils, discrete inputs, holding registers, and input registers
- **Server-side datastore management** - Populate and read all 4 register types on server instances
- **Multiple concurrent connections** - Manage multiple Modbus clients and servers simultaneously
- **Robust error handling** - Comprehensive validation and user-friendly error messages
- **Property-based testing** - Extensive test coverage ensuring reliability
- **FastMCP integration** - Built on the latest MCP protocol standards
- **PyModbus 3.11.4 Compatible** - Fully updated for the latest pymodbus API

## PyModbus 3.11.4 Compatibility

This server is fully compatible with **pymodbus 3.11.4**, the latest stable release. Key updates include:

### API Changes Implemented
- **Parameter naming**: Changed from `slave=` to `device_id=` for all Modbus operations
- **Keyword-only arguments**: Updated method calls to use `count=count` syntax
- **Exception handling**: Removed obsolete exception classes and updated error handling

### What This Means for Users
- ✅ **Stable and tested**: All operations verified against live Modbus devices
- ✅ **Future-proof**: Compatible with the latest pymodbus features and fixes
- ✅ **Better error messages**: Improved exception handling for clearer diagnostics
- ✅ **Correct bit ordering**: Benefits from pymodbus 3.11.0 bit handling corrections

For more details on pymodbus changes, see [PYMODBUS_3.11.4_UPGRADE.md](PYMODBUS_3.11.4_UPGRADE.md).

## Quick Start

### Installation

#### Method 1: Standard Installation (Recommended)

```bash
# Install from source
git clone https://github.com/alejoseb/ModbusMCP.git
cd ModbusMCP
pip install -e .

# For development
pip install -e ".[dev]"
```

**Note**: This version requires pymodbus 3.11.4. If you have an older version installed, upgrade with:
```bash
pip install --upgrade pymodbus==3.11.4
```

#### Method 2: If pip installation fails (Windows)

If you encounter "No module named pip" or similar errors:

```cmd
# Try with python -m pip
python -m pip install -e .

# Or install dependencies manually
python -m pip install fastmcp>=0.2.0 pymodbus>=3.6.0 pyserial>=3.5
python -m pip install .
```

#### Method 3: Direct execution without installation

If installation continues to fail, use the provided scripts:

**Windows (Command Prompt):**
```cmd
run_server.bat --version
```

**Windows (PowerShell):**
```powershell
.\run_server.ps1 --version
```

**Manual execution:**
```cmd
# Install dependencies first
python -m pip install fastmcp>=0.2.0 pymodbus==3.11.4 pyserial==3.5

# Run directly
python -m src.modbus_mcp_server.cli
```

### Basic Usage

```bash
# Start the MCP server (stdio transport)
modbus-mcp-server

# Start with custom configuration
modbus-mcp-server --config config.json

# Start with debug logging
modbus-mcp-server --log-level DEBUG
```

## IDE Integration

### Visual Studio Code

#### 1. Install the MCP Extension

Install the official MCP extension for Visual Studio Code from the marketplace.

#### 2. Configure MCP Settings

Add the Modbus MCP server to your VS Code settings. Open your `settings.json` and add:

```json
{
  "mcp.servers": {
    "modbus": {
      "command": "modbus-mcp-server",
      "args": ["--log-level", "INFO"],
      "env": {
        "MODBUS_MCP_LOG_FILE": "/tmp/modbus-mcp.log"
      }
    }
  }
}
```

#### 3. Alternative Configuration with Custom Path

If you installed the server in a virtual environment:

```json
{
  "mcp.servers": {
    "modbus": {
      "command": "/path/to/venv/bin/modbus-mcp-server",
      "args": ["--config", "/path/to/modbus-config.json"],
      "env": {
        "MODBUS_MCP_DEFAULT_TIMEOUT": "5.0",
        "MODBUS_MCP_MAX_CLIENTS": "10"
      }
    }
  }
}
```

#### 4. Using the Server

Once configured, you can use Modbus functionality in VS Code:

1. Open the Command Palette (`Ctrl+Shift+P` / `Cmd+Shift+P`)
2. Type "MCP: " to see available MCP commands
3. Use the AI assistant with Modbus capabilities

**Example conversation:**
```
You: "List available serial ports on this system"
AI: [Uses list_serial_ports tool to show COM1, COM3, etc.]

You: "Connect to Modbus RTU device on COM3 with baud rate 9600 and slave ID 1"
AI: [Uses create_rtu_client tool to establish connection]

You: "Read holding registers 40001 to 40010 from the connected device"
AI: [Uses read_holding_registers tool to get values]
```

### Kiro IDE

#### 1. Configure MCP Server

In Kiro, add the Modbus MCP server to your MCP configuration. Create or edit `.kiro/settings/mcp.json`:

```json
{
  "mcpServers": {
    "modbus": {
      "command": "modbus-mcp-server",
      "args": ["--transport", "stdio"],
      "env": {
        "MODBUS_MCP_LOG_LEVEL": "INFO"
      },
      "disabled": true,
      "autoApprove": [
        "list_serial_ports",
        "list_clients"
      ]
    }
  }
}
```

#### 2. Advanced Configuration

For production use with custom settings:

```json
{
  "mcpServers": {
    "modbus": {
      "command": "modbus-mcp-server",
      "args": [
        "--config", "/path/to/modbus-config.json",
        "--log-level", "WARNING",
        "--max-clients", "20"
      ],
      "env": {
        "MODBUS_MCP_DEFAULT_TIMEOUT": "10.0",
        "MODBUS_MCP_LOG_FILE": "/var/log/modbus-mcp.log"
      },
      "disabled": false,
      "autoApprove": [
        "list_serial_ports",
        "list_clients",
        "read_coils",
        "read_discrete_inputs",
        "read_holding_registers",
        "read_input_registers"
      ]
    }
  }
}
```

#### 3. Using in Kiro

After configuration, restart Kiro or reconnect the MCP server. You can then:

1. Use natural language to interact with Modbus devices
2. Ask Kiro to discover serial ports, create connections, and read/write data
3. Leverage Kiro's context awareness for complex automation tasks

**Example workflow:**
```
You: "I need to monitor temperature sensors connected via Modbus RTU on COM1"
Kiro: [Discovers COM1, creates RTU client, sets up monitoring]

You: "Read the temperature values every 30 seconds and alert me if any exceed 75°C"
Kiro: [Sets up periodic reading with alerting logic]
```

## Available MCP Tools

The server exposes the following tools through the MCP protocol:

### Client Connection Management
- `list_serial_ports` - Discover available serial ports
- `create_rtu_client` - Create Modbus RTU client connection
- `create_tcp_client` - Create Modbus TCP client connection
- `close_client` - Close and cleanup client connection
- `list_clients` - List active client connections

### Client Read Operations
- `read_coils` - Read coil values (digital outputs)
- `read_discrete_inputs` - Read discrete input values (digital inputs)
- `read_holding_registers` - Read holding register values (analog/config data)
- `read_input_registers` - Read input register values (sensor data)

### Client Write Operations
- `write_coils` - Write coil values (control digital outputs)
- `write_holding_registers` - Write holding register values (set parameters)

### Server (Slave) Lifecycle
- `create_tcp_server` - Start a Modbus TCP slave on a given host and port
- `create_rtu_server` - Start a Modbus RTU slave on a serial port
- `stop_server` - Stop a running server by ID
- `list_servers` - List all active server instances

### Server Datastore Operations
- `server_read_coils` / `server_write_coils` - Read/write coil values in a server's datastore
- `server_read_discrete_inputs` / `server_write_discrete_inputs` - Read/set discrete input values
- `server_read_holding_registers` / `server_write_holding_registers` - Read/write holding register values
- `server_read_input_registers` / `server_write_input_registers` - Read/set input register values

> **Note:** Server-side write operations for discrete inputs and input registers allow the server owner to populate data that is normally read-only from the client perspective.

## Configuration

### Configuration File

Create a JSON configuration file for advanced settings:

```json
{
  "server": {
    "host": "localhost",
    "port": 8000,
    "transport": "stdio",
    "log_level": "INFO",
    "log_file": null
  },
  "modbus": {
    "default_timeout": 3.0,
    "max_clients": 50,
    "default_tcp_port": 502,
    "default_baudrate": 9600,
    "default_bytesize": 8,
    "default_parity": "N",
    "default_stopbits": 1
  },
  "limits": {
    "max_coil_count": 2000,
    "max_discrete_input_count": 2000,
    "max_holding_register_count": 125,
    "max_input_register_count": 125,
    "max_write_coil_count": 1968,
    "max_write_register_count": 123
  }
}
```

### Environment Variables

Configure the server using environment variables:

```bash
# Server settings
export MODBUS_MCP_HOST=localhost
export MODBUS_MCP_PORT=8000
export MODBUS_MCP_TRANSPORT=stdio
export MODBUS_MCP_LOG_LEVEL=INFO
export MODBUS_MCP_LOG_FILE=/var/log/modbus-mcp.log

# Modbus settings
export MODBUS_MCP_DEFAULT_TIMEOUT=5.0
export MODBUS_MCP_MAX_CLIENTS=25
export MODBUS_MCP_DEFAULT_TCP_PORT=502
export MODBUS_MCP_DEFAULT_BAUDRATE=19200

# Start server
modbus-mcp-server
```

## Examples

### Example 1: Industrial Temperature Monitoring

```python
# Through MCP, you can ask the AI assistant:
"Connect to the temperature controller on COM3 at 9600 baud, slave ID 1, 
then read holding registers 40001-40004 to get the current temperatures 
from all four zones."
```

### Example 2: PLC Control System

```python
# Control a PLC via Modbus TCP:
"Connect to PLC at 192.168.1.100 port 502, slave ID 1. 
Read coils 1-16 to check current output states, 
then set coil 5 to ON to start the conveyor motor."
```

### Example 3: Multi-Device Monitoring

```python
# Monitor multiple devices:
"List all available serial ports, then connect to devices on COM1 and COM3.
Read input registers from both devices every 10 seconds and compare the values."
```

### Example 4: Simulating a Modbus Device

```python
# Start a Modbus TCP server to simulate a temperature sensor:
"Create a TCP server on port 5020 with slave ID 1.
Set holding registers 0-3 to values [2500, 2650, 2700, 2550]
representing temperatures in tenths of degrees.
Then connect a client to verify the values can be read."
```

### Example 5: Device Testing and Bridging

```python
# Use server + client together for testing:
"Start a TCP server on 127.0.0.1:5020 with slave ID 1,
populate its input registers 0-9 with test sensor data,
then create a TCP client to connect to it and verify all values are correct."
```

## Troubleshooting

### Installation Issues

#### "No module named pip" Error

This is a common Windows issue. Try these solutions in order:

1. **Use python -m pip instead:**
   ```cmd
   python -m pip install -e .
   ```

2. **Reinstall pip:**
   ```cmd
   # Download get-pip.py from https://bootstrap.pypa.io/get-pip.py
   python get-pip.py
   python -m pip install -e .
   ```

3. **Use virtual environment:**
   ```cmd
   python -m venv modbus_env
   modbus_env\Scripts\activate
   python -m pip install --upgrade pip
   python -m pip install -e .
   ```

4. **Direct execution (no installation):**
   ```cmd
   # Use the provided batch file
   run_server.bat --version
   
   # Or manually
   python -m pip install fastmcp>=0.2.0 pymodbus==3.11.4 pyserial==3.5
   python -m src.modbus_mcp_server.cli
   ```

### Common Issues

1. **Serial Port Access Denied**
   ```bash
   # On Linux, add user to dialout group
   sudo usermod -a -G dialout $USER
   # Logout and login again
   ```

2. **TCP Connection Refused**
   - Check if the Modbus device is reachable: `ping <device-ip>`
   - Verify the port is correct (default: 502)
   - Check firewall settings

3. **Invalid Slave ID**
   - Modbus slave IDs must be between 1-247
   - Verify the device's configured slave ID

4. **Timeout Errors**
   - Increase timeout: `--default-timeout 10.0`
   - Check physical connections and cable integrity
   - Verify baud rate and communication parameters

### Debug Mode

Enable debug logging for detailed troubleshooting:

```bash
modbus-mcp-server --log-level DEBUG --log-file debug.log
```

### Testing Connection

Use the built-in tools to test connectivity:

```bash
# Generate and use test configuration
modbus-mcp-server --generate-config test-config.json
modbus-mcp-server --config test-config.json --show-config
```

## Development

### Testing Status

✅ **All MCP tools tested and verified** (2026-02-12)

#### Client Tools

| Tool | Status | Notes |
|------|--------|-------|
| `list_serial_ports` | ✅ Pass | Successfully lists available serial ports |
| `create_tcp_client` | ✅ Pass | Connects to TCP server at 127.0.0.1:5020 |
| `create_rtu_client` | ✅ Pass | Creates RTU client connections |
| `read_holding_registers` | ✅ Pass | Read and verified values [100, 200, 300, 400, 500] |
| `write_holding_registers` | ✅ Pass | Write operation confirmed with read-back |
| `read_coils` | ✅ Pass | Successfully reads coil states |
| `write_coils` | ✅ Pass | Write operation confirmed with read-back |
| `read_discrete_inputs` | ✅ Pass | Successfully reads discrete input states |
| `read_input_registers` | ✅ Pass | Successfully reads input register values |
| `list_clients` | ✅ Pass | Lists active connections with details |
| `close_client` | ✅ Pass | Properly closes and cleans up connections |

#### Server (Slave) Tools

| Tool | Status | Notes |
|------|--------|-------|
| `create_tcp_server` | ✅ Pass | Starts TCP slave, works from within MCP event loop |
| `create_rtu_server` | ✅ Pass | Starts RTU slave on serial port |
| `stop_server` | ✅ Pass | Stops server and releases TCP/serial port |
| `list_servers` | ✅ Pass | Lists active servers with connection details |
| `server_read_coils` | ✅ Pass | Reads coil values from server datastore |
| `server_write_coils` | ✅ Pass | Writes coils, verified via client read-back |
| `server_read_discrete_inputs` | ✅ Pass | Reads discrete inputs from datastore |
| `server_write_discrete_inputs` | ✅ Pass | Populates discrete inputs, verified via client |
| `server_read_holding_registers` | ✅ Pass | Reads holding registers from datastore |
| `server_write_holding_registers` | ✅ Pass | Writes registers, verified via client read-back |
| `server_read_input_registers` | ✅ Pass | Reads input registers from datastore |
| `server_write_input_registers` | ✅ Pass | Populates input registers, verified via client |

#### End-to-End Tests
- ✅ Server create → populate datastore → client connect → client read → values match
- ✅ Server stop → port freed → new server on same port succeeds
- ✅ Server creation from inside running async event loop (MCP framework scenario)

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/modbus_mcp_server

# Run property-based tests with more examples
pytest -v tests/ -k "property"
```

### Code Quality

```bash
# Format code
black src tests
isort src tests

# Type checking
mypy src

# Linting
flake8 src tests
```

### Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## Requirements

- **Python**: 3.8 or higher
- **Dependencies**:
  - fastMCP >= 0.2.0
  - pymodbus == 3.11.4
  - pyserial == 3.5
- **Operating System**: Windows, macOS, Linux
- **Hardware**: Serial ports (for RTU) or network access (for TCP)

## Version History

### v0.3.0 (2026-02-12)
- **Modbus Server (Slave) Support** - 12 new MCP tools for running Modbus TCP and RTU servers
  - Create, stop, and list server instances
  - Read/write all 4 register types (coils, discrete inputs, holding registers, input registers) on server datastores
  - Server-side populate for read-only register types (discrete inputs, input registers)
- **Async-safe architecture** - Each server runs in its own thread with a dedicated event loop, compatible with the MCP framework's async context
- **Port conflict tracking** - Prevents binding the same TCP or serial port twice
- **End-to-end verified** - Server + client communication tested for all register types

### v0.2.0 (2026-02-05)
- **Updated to pymodbus 3.11.4** - Full compatibility with latest pymodbus release
- **API Changes**:
  - Changed `slave=` parameter to `device_id=` in all Modbus operations
  - Updated method signatures to use keyword-only arguments for `count` parameter
  - Removed obsolete exception classes (`InvalidMessageReceivedException`, `MessageRegisterException`)
- **Testing**: All MCP tools tested and verified against live Modbus TCP server
- **Improvements**: Enhanced error handling and exception management

### v0.1.0 (Initial Release)
- Initial implementation with pymodbus 3.6.0
- Support for Modbus RTU and TCP clients
- Complete read/write operations for all Modbus data types
- Serial port discovery and management
- FastMCP integration

## License

MIT License - see LICENSE file for details.

## Author

**Alejandro Mera**  
Email: alejoseb@gmail.com

## Support

For issues and questions:
1. Check the troubleshooting section above
2. Review the [fastMCP documentation](https://github.com/jlowin/fastmcp)
3. Check [pymodbus documentation](https://pymodbus.readthedocs.io/)
4. Open an issue in this repository
