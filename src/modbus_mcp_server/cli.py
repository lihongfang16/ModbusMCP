"""Command-line interface for the Modbus MCP Server."""

import argparse
import sys
from pathlib import Path
from typing import List, Optional

from .config import create_default_config_file, load_config
from .main import main


def create_parser() -> argparse.ArgumentParser:
    """Create command-line argument parser."""
    parser = argparse.ArgumentParser(
        prog="modbus-mcp-server",
        description="Modbus MCP Server - Expose Modbus client functionality via MCP",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Start server with default settings (stdio transport)
  modbus-mcp-server

  # Start server with custom configuration file
  modbus-mcp-server --config /path/to/config.json

  # Start server with specific log level
  modbus-mcp-server --log-level DEBUG

  # Generate default configuration file
  modbus-mcp-server --generate-config config.json

  # Show current configuration (without starting server)
  modbus-mcp-server --show-config

Environment Variables:
  MODBUS_MCP_TRANSPORT         Transport type (stdio)
  MODBUS_MCP_LOG_LEVEL         Log level (DEBUG, INFO, WARNING, ERROR)
  MODBUS_MCP_LOG_FILE          Log file path
  MODBUS_MCP_DEFAULT_TIMEOUT   Default operation timeout in seconds
  MODBUS_MCP_MAX_CLIENTS       Maximum concurrent clients
  MODBUS_MCP_WEB_UI            Enable web UI interface (true/false)
  MODBUS_MCP_WEB_UI_PORT       Web UI server port (default: 8090)
  
For a complete list of environment variables, see the documentation.
        """,
    )
    
    # Configuration options
    config_group = parser.add_argument_group("Configuration")
    config_group.add_argument(
        "-c", "--config",
        type=str,
        help="Path to configuration file (JSON format)"
    )
    config_group.add_argument(
        "--generate-config",
        type=str,
        metavar="FILE",
        help="Generate default configuration file and exit"
    )
    config_group.add_argument(
        "--show-config",
        action="store_true",
        help="Show current configuration and exit"
    )
    
    # Server options
    server_group = parser.add_argument_group("Server Options")
    server_group.add_argument(
        "--host",
        type=str,
        help="Server host address (for reference only, stdio transport ignores this)"
    )
    server_group.add_argument(
        "--port",
        type=int,
        help="Server port number (for reference only, stdio transport ignores this)"
    )
    server_group.add_argument(
        "--transport",
        choices=["stdio", "sse"],
        help="Transport type (overrides config file)"
    )
    
    # Logging options
    logging_group = parser.add_argument_group("Logging Options")
    logging_group.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Set logging level (overrides config file)"
    )
    logging_group.add_argument(
        "--log-file",
        type=str,
        help="Log file path (overrides config file)"
    )
    logging_group.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Suppress all output except errors"
    )
    logging_group.add_argument(
        "--verbose", "-v",
        action="count",
        default=0,
        help="Increase verbosity (-v for INFO, -vv for DEBUG)"
    )
    
    # Modbus options
    modbus_group = parser.add_argument_group("Modbus Options")
    modbus_group.add_argument(
        "--default-timeout",
        type=float,
        help="Default operation timeout in seconds"
    )
    modbus_group.add_argument(
        "--max-clients",
        type=int,
        help="Maximum number of concurrent clients"
    )
    
    # Web UI options
    web_ui_group = parser.add_argument_group("Web UI Options")
    web_ui_group.add_argument(
        "--web-ui",
        action="store_true",
        help="Enable web UI interface (requires fastapi/uvicorn)"
    )
    web_ui_group.add_argument(
        "--web-ui-port",
        type=int,
        default=8090,
        help="Web UI server port (default: 8090)"
    )
    
    # Version and help
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 0.3.0"
    )
    
    return parser


def apply_cli_overrides(config, args: argparse.Namespace) -> None:
    """Apply command-line argument overrides to configuration.
    
    Args:
        config: ServerConfig instance to modify
        args: Parsed command-line arguments
    """
    # Server options
    # Note: host/port are accepted for backward compatibility but ignored for stdio transport
    if args.host is not None:
        config.host = args.host
    if args.port is not None:
        config.port = args.port
    if args.transport is not None:
        config.transport = args.transport
    
    # Logging options
    if args.log_level is not None:
        config.log_level = args.log_level
    if args.log_file is not None:
        config.log_file = args.log_file
    
    # Handle quiet and verbose flags
    if args.quiet:
        config.log_level = "ERROR"
    elif args.verbose == 1:
        config.log_level = "INFO"
    elif args.verbose >= 2:
        config.log_level = "DEBUG"
    
    # Modbus options
    if args.default_timeout is not None:
        config.default_timeout = args.default_timeout
    if args.max_clients is not None:
        config.max_clients = args.max_clients
    
    # Web UI options
    if args.web_ui:
        config.enable_web_ui = True
    if args.web_ui_port != 8090:
        config.web_ui_port = args.web_ui_port


def show_config(config) -> None:
    """Display current configuration."""
    print("Current Configuration:")
    print("=" * 50)
    
    # Server settings
    print(f"Host:                    {config.host}")
    print(f"Port:                    {config.port}")
    print(f"Transport:               {config.transport}")
    print()
    
    # Logging settings
    print(f"Log Level:               {config.log_level}")
    print(f"Log Format:              {config.log_format}")
    print(f"Log File:                {config.log_file or 'None (console only)'}")
    print()
    
    # Connection settings
    print(f"Default Timeout:         {config.default_timeout}s")
    print(f"Max Clients:             {config.max_clients}")
    print(f"Cleanup Interval:        {config.cleanup_interval}s")
    print()
    
    # Modbus settings
    print(f"Default TCP Port:        {config.default_tcp_port}")
    print(f"Default Baudrate:        {config.default_baudrate}")
    print(f"Default Bytesize:        {config.default_bytesize}")
    print(f"Default Parity:          {config.default_parity}")
    print(f"Default Stopbits:        {config.default_stopbits}")
    print()
    
    # Limits
    print(f"Max Coil Count:          {config.max_coil_count}")
    print(f"Max Discrete Inputs:     {config.max_discrete_input_count}")
    print(f"Max Holding Registers:   {config.max_holding_register_count}")
    print(f"Max Input Registers:     {config.max_input_register_count}")
    print(f"Max Write Coils:         {config.max_write_coil_count}")
    print(f"Max Write Registers:     {config.max_write_register_count}")
    print()
    
    # Advanced settings
    print(f"Enable Metrics:          {config.enable_metrics}")
    if config.enable_metrics:
        print(f"Metrics Port:            {config.metrics_port}")
    print(f"Enable Health Check:     {config.enable_health_check}")
    if config.enable_health_check:
        print(f"Health Check Port:       {config.health_check_port}")
    print()
    
    # Web UI settings
    print(f"Enable Web UI:           {config.enable_web_ui}")
    if config.enable_web_ui:
        print(f"Web UI Port:             {config.web_ui_port}")


def cli_main(argv: Optional[List[str]] = None) -> int:
    """Main CLI entry point.
    
    Args:
        argv: Command-line arguments (defaults to sys.argv)
        
    Returns:
        Exit code (0 for success, non-zero for error)
    """
    parser = create_parser()
    args = parser.parse_args(argv)
    
    try:
        # Handle special commands first
        if args.generate_config:
            create_default_config_file(args.generate_config)
            print(f"Default configuration file created: {args.generate_config}")
            return 0
        
        # Load configuration
        config = load_config(args.config)
        
        # Apply CLI overrides
        apply_cli_overrides(config, args)
        
        # Handle show config command
        if args.show_config:
            show_config(config)
            return 0
        
        # Start the server
        main(args.config, config)
        return 0
        
    except KeyboardInterrupt:
        print("\nServer stopped by user", file=sys.stderr)
        return 130  # Standard exit code for SIGINT
    except FileNotFoundError as e:
        print(f"Error: Configuration file not found: {e}", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"Error: Invalid configuration: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(cli_main())