# Modbus MCP Server

An MCP (Model Context Protocol) server that provides Modbus client functionality, enabling LLM applications to interact with Modbus RTU and TCP devices through a standardized interface. This server acts as a bridge between AI assistants and industrial automation systems, PLCs, sensors, and other Modbus-enabled devices.

## Features

- **Modbus RTU and TCP client support** - Connect to serial and network Modbus devices
- **Serial port discovery and management** - Automatically detect available serial ports
- **Comprehensive read/write operations** - Support for coils, discrete inputs, holding registers, and input registers
- **Multiple concurrent connections** - Manage multiple Modbus devices simultaneously
- **Robust error handling** - Comprehensive validation and user-friendly error messages
- **Property-based testing** - Extensive test coverage ensuring reliability
- **FastMCP integration** - Built on the latest MCP protocol standards

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
python -m pip install fastmcp>=0.2.0 pymodbus>=3.6.0 pyserial>=3.5

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
      "disabled": false,
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

### Connection Management
- `list_serial_ports` - Discover available serial ports
- `create_rtu_client` - Create Modbus RTU client connection
- `create_tcp_client` - Create Modbus TCP client connection
- `close_client` - Close and cleanup client connection
- `list_clients` - List active client connections

### Read Operations
- `read_coils` - Read coil values (digital outputs)
- `read_discrete_inputs` - Read discrete input values (digital inputs)
- `read_holding_registers` - Read holding register values (analog/config data)
- `read_input_registers` - Read input register values (sensor data)

### Write Operations
- `write_coils` - Write coil values (control digital outputs)
- `write_holding_registers` - Write holding register values (set parameters)

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
   python -m pip install fastmcp>=0.2.0 pymodbus>=3.6.0 pyserial>=3.5
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
  - pymodbus >= 3.6.0
  - pyserial >= 3.5
- **Operating System**: Windows, macOS, Linux
- **Hardware**: Serial ports (for RTU) or network access (for TCP)

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
