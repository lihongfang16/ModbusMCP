# Modbus MCP Server Examples

This directory contains example configurations and usage scenarios for the Modbus MCP Server.

## Files

### Configuration Examples

- **`config.json`** - Complete server configuration file with all available options
- **`vscode-settings.json`** - VS Code MCP server configuration
- **`kiro-mcp.json`** - Kiro IDE MCP server configuration

### Documentation

- **`usage-examples.md`** - Comprehensive usage examples and scenarios
- **`README.md`** - This file

## Quick Setup

### For Visual Studio Code

1. Copy the contents of `vscode-settings.json` to your VS Code `settings.json`
2. Adjust paths and parameters as needed for your environment
3. Restart VS Code and the MCP extension will load the Modbus server

### For Kiro IDE

1. Copy `kiro-mcp.json` to `.kiro/settings/mcp.json` in your workspace
2. Modify the configuration as needed
3. Restart Kiro or reconnect the MCP server from the MCP panel

### Custom Configuration

1. Copy `config.json` to your desired location
2. Modify settings for your environment
3. Start the server with: `modbus-mcp-server --config /path/to/config.json`

## Environment-Specific Examples

### Development Environment

```json
{
  "mcpServers": {
    "modbus": {
      "command": "modbus-mcp-server",
      "args": ["--log-level", "DEBUG", "--max-clients", "5"],
      "env": {
        "MODBUS_MCP_LOG_FILE": "./debug.log"
      }
    }
  }
}
```

### Production Environment

```json
{
  "mcpServers": {
    "modbus": {
      "command": "/opt/modbus-mcp/bin/modbus-mcp-server",
      "args": [
        "--config", "/etc/modbus-mcp/config.json",
        "--log-level", "WARNING"
      ],
      "env": {
        "MODBUS_MCP_LOG_FILE": "/var/log/modbus-mcp.log",
        "MODBUS_MCP_MAX_CLIENTS": "100"
      }
    }
  }
}
```

### Testing Environment

```json
{
  "mcpServers": {
    "modbus": {
      "command": "modbus-mcp-server",
      "args": ["--log-level", "INFO"],
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

## Common Use Cases

### Industrial Automation
- PLC monitoring and control
- Sensor data collection
- Process automation
- Equipment status monitoring

### Energy Management
- Power meter reading
- Load monitoring
- Demand response
- Energy efficiency tracking

### Building Automation
- HVAC control
- Lighting systems
- Security systems
- Environmental monitoring

### Laboratory Equipment
- Instrument control
- Data acquisition
- Test automation
- Quality control

## Tips

1. **Start Simple**: Begin with basic read operations before attempting writes
2. **Use Auto-Approve**: Add frequently used tools to `autoApprove` for smoother operation
3. **Monitor Logs**: Enable logging to troubleshoot connection issues
4. **Test Connections**: Use `list_serial_ports` and `list_clients` to verify setup
5. **Adjust Timeouts**: Increase timeouts for slow or distant devices

## Support

For additional help:
- Check the main README.md for troubleshooting
- Review the usage examples for common scenarios
- Consult the Modbus device documentation for specific parameters