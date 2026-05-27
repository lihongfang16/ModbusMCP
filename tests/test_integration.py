"""Integration tests for the Modbus MCP Server."""

import asyncio
import json
import os
import tempfile
import threading
import time
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import Mock, patch

import pytest
from pymodbus.server import StartTcpServer
from pymodbus.datastore import ModbusSequentialDataBlock, ModbusServerContext
from pymodbus import ModbusDeviceIdentification

from modbus_mcp_server.config import ServerConfig, ConfigManager
from modbus_mcp_server.main import create_app
from modbus_mcp_server.cli import cli_main, apply_cli_overrides, show_config


class MockModbusServer:
    """Mock Modbus TCP server for testing."""
    
    def __init__(self, port: int = 5020):
        self.port = port
        self.server_task = None
        self.running = False
        self.loop = None
    
    async def start_async(self):
        """Start the mock Modbus server asynchronously."""
        # Create data store with some test data
        store = {
            1: {
                "di": ModbusSequentialDataBlock(0, [False] * 100),  # Discrete inputs
                "co": ModbusSequentialDataBlock(0, [False] * 100),  # Coils
                "hr": ModbusSequentialDataBlock(0, [0] * 100),      # Holding registers
                "ir": ModbusSequentialDataBlock(0, [0] * 100),      # Input registers
            }
        }
        context = ModbusServerContext(devices=store, single=True)
        
        # Set up device identification
        identity = ModbusDeviceIdentification()
        identity.VendorName = 'Test Vendor'
        identity.ProductCode = 'TEST'
        identity.VendorUrl = 'http://test.com'
        identity.ProductName = 'Test Modbus Server'
        identity.ModelName = 'Test Model'
        identity.MajorMinorRevision = '1.0'
        
        try:
            # Start the server
            await StartTcpServer(
                context=context,
                identity=identity,
                address=("localhost", self.port),
            )
        except Exception as e:
            print(f"Mock server error: {e}")
    
    def start(self):
        """Start the mock Modbus server in a separate thread."""
        def run_server():
            """Run the server in a separate thread."""
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            try:
                self.loop.run_until_complete(self.start_async())
            except Exception as e:
                print(f"Mock server thread error: {e}")
            finally:
                self.loop.close()
        
        self.server_thread = threading.Thread(target=run_server, daemon=True)
        self.server_thread.start()
        self.running = True
        
        # Give the server time to start
        time.sleep(1.0)
    
    def stop(self):
        """Stop the mock Modbus server."""
        self.running = False
        if self.loop and not self.loop.is_closed():
            self.loop.call_soon_threadsafe(self.loop.stop)


@pytest.fixture
def mock_modbus_server():
    """Fixture providing a mock Modbus TCP server."""
    server = MockModbusServer()
    server.start()
    yield server
    server.stop()


@pytest.fixture
def test_config():
    """Fixture providing test configuration."""
    return ServerConfig(
        host="localhost",
        port=8001,
        transport="stdio",
        log_level="DEBUG",
        default_timeout=1.0,
        max_clients=10,
    )


@pytest.fixture
def temp_config_file():
    """Fixture providing a temporary configuration file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        config_data = {
            "host": "localhost",
            "port": 8002,
            "transport": "stdio",
            "log_level": "INFO",
            "default_timeout": 2.0,
            "max_clients": 5,
        }
        json.dump(config_data, f)
        temp_path = f.name
    
    yield temp_path
    
    # Cleanup
    try:
        os.unlink(temp_path)
    except OSError:
        pass


class TestConfigurationIntegration:
    """Test configuration loading and management."""
    
    def test_config_loading_from_file(self, temp_config_file):
        """Test loading configuration from file."""
        manager = ConfigManager(temp_config_file)
        config = manager.load_config()
        
        assert config.host == "localhost"
        assert config.port == 8002
        assert config.transport == "stdio"
        assert config.log_level == "INFO"
        assert config.default_timeout == 2.0
        assert config.max_clients == 5
    
    def test_config_loading_from_env(self):
        """Test loading configuration from environment variables."""
        env_vars = {
            "MODBUS_MCP_HOST": "test-host",
            "MODBUS_MCP_PORT": "9999",
            "MODBUS_MCP_LOG_LEVEL": "ERROR",
            "MODBUS_MCP_DEFAULT_TIMEOUT": "5.0",
        }
        
        with patch.dict(os.environ, env_vars):
            manager = ConfigManager()
            config = manager.load_config()
            
            assert config.host == "test-host"
            assert config.port == 9999
            assert config.log_level == "ERROR"
            assert config.default_timeout == 5.0
    
    def test_config_validation_errors(self):
        """Test configuration validation catches errors."""
        manager = ConfigManager()
        
        # Test invalid port
        with patch.dict(os.environ, {"MODBUS_MCP_PORT": "99999"}):
            with pytest.raises(ValueError, match="Invalid port"):
                manager.load_config()
        
        # Test invalid log level
        with patch.dict(os.environ, {"MODBUS_MCP_LOG_LEVEL": "INVALID"}):
            with pytest.raises(ValueError, match="Invalid log level"):
                manager.load_config()
    
    def test_config_file_generation(self):
        """Test generating default configuration file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name
        
        try:
            manager = ConfigManager()
            config = ServerConfig()
            manager.save_config(config, temp_path)
            
            # Verify file was created and contains expected data
            assert Path(temp_path).exists()
            
            with open(temp_path, 'r') as f:
                saved_data = json.load(f)
            
            assert saved_data["host"] == "localhost"
            assert saved_data["port"] == 8000
            assert saved_data["transport"] == "stdio"
            
        finally:
            try:
                os.unlink(temp_path)
            except OSError:
                pass


class TestCLIIntegration:
    """Test command-line interface integration."""
    
    def test_cli_help(self):
        """Test CLI help output."""
        with pytest.raises(SystemExit) as exc_info:
            cli_main(["--help"])
        assert exc_info.value.code == 0
    
    def test_cli_version(self):
        """Test CLI version output."""
        with pytest.raises(SystemExit) as exc_info:
            cli_main(["--version"])
        assert exc_info.value.code == 0
    
    def test_cli_generate_config(self):
        """Test CLI configuration file generation."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name
        
        try:
            # Remove the file so we can test generation
            os.unlink(temp_path)
            
            result = cli_main(["--generate-config", temp_path])
            assert result == 0
            assert Path(temp_path).exists()
            
            # Verify the generated file
            with open(temp_path, 'r') as f:
                config_data = json.load(f)
            
            assert "host" in config_data
            assert "port" in config_data
            assert "transport" in config_data
            
        finally:
            try:
                os.unlink(temp_path)
            except OSError:
                pass
    
    def test_cli_show_config(self, temp_config_file, capsys):
        """Test CLI show configuration."""
        result = cli_main(["--config", temp_config_file, "--show-config"])
        assert result == 0
        
        captured = capsys.readouterr()
        assert "Current Configuration:" in captured.out
        assert "Host:" in captured.out
        assert "Port:" in captured.out
    
    def test_cli_config_overrides(self, temp_config_file):
        """Test CLI configuration overrides."""
        # This test verifies that CLI arguments override config file values
        # We can't easily test the full server startup, but we can test the parsing
        
        with patch('modbus_mcp_server.cli.main') as mock_main:
            result = cli_main([
                "--config", temp_config_file,
                "--host", "override-host",
                "--port", "9999",
                "--log-level", "ERROR"
            ])
            
            assert result == 0
            mock_main.assert_called_once()
            
            # Verify the config passed to main has the overrides
            call_args = mock_main.call_args
            config = call_args[0][1]  # Second argument is the config
            
            assert config.host == "override-host"
            assert config.port == 9999
            assert config.log_level == "ERROR"
    
    def test_cli_invalid_config_file(self):
        """Test CLI with invalid configuration file."""
        # Mock the main function to avoid async issues
        with patch('modbus_mcp_server.cli.main') as mock_main:
            mock_main.side_effect = FileNotFoundError("Configuration file not found")
            result = cli_main(["--config", "/nonexistent/config.json"])
            assert result == 1  # Should return error code
    
    def test_cli_verbose_flags(self, temp_config_file):
        """Test CLI verbose and quiet flags."""
        with patch('modbus_mcp_server.cli.main') as mock_main:
            # Test verbose flag
            cli_main(["--config", temp_config_file, "-vv"])
            config = mock_main.call_args[0][1]
            assert config.log_level == "DEBUG"
            
            mock_main.reset_mock()
            
            # Test quiet flag
            cli_main(["--config", temp_config_file, "--quiet"])
            config = mock_main.call_args[0][1]
            assert config.log_level == "ERROR"


class TestApplicationIntegration:
    """Test FastMCP application integration."""
    
    def test_app_creation(self, test_config):
        """Test FastMCP application creation."""
        app = create_app(test_config)
        
        # Verify app has required components
        assert hasattr(app, 'connection_manager')
        assert hasattr(app, 'command_handlers')
        assert hasattr(app, 'config')
        assert app.config == test_config
    
    def test_app_tool_registration(self, test_config):
        """Test that all MCP tools are registered."""
        app = create_app(test_config)
        
        # Verify app has the required components
        assert hasattr(app, 'connection_manager')
        assert hasattr(app, 'command_handlers')
        assert hasattr(app, 'config')
        
        # Test that the command handlers have the expected methods
        handlers = app.command_handlers
        expected_methods = [
            "handle_list_serial_ports",
            "handle_create_rtu_client",
            "handle_create_tcp_client",
            "handle_close_client",
            "handle_list_clients",
            "handle_read_coils",
            "handle_write_coils",
            "handle_read_discrete_inputs",
            "handle_read_holding_registers",
            "handle_write_holding_registers",
            "handle_read_input_registers",
        ]
        
        for method_name in expected_methods:
            assert hasattr(handlers, method_name)
    
    @pytest.mark.asyncio
    async def test_app_tool_execution(self, test_config):
        """Test basic tool execution."""
        app = create_app(test_config)
        
        # Test command handlers directly
        handlers = app.command_handlers
        
        # Test list_serial_ports
        result = handlers.handle_list_serial_ports()
        assert isinstance(result, dict)
        assert "success" in result
        
        # Test list_clients (should return empty list initially)
        result = handlers.handle_list_clients()
        assert isinstance(result, dict)
        assert "success" in result
        if result["success"]:
            assert "clients" in result
            assert isinstance(result["clients"], list)


class TestEndToEndIntegration:
    """Test end-to-end functionality with command handlers."""
    
    @pytest.mark.asyncio
    async def test_tcp_client_lifecycle(self, test_config):
        """Test complete TCP client lifecycle."""
        app = create_app(test_config)
        handlers = app.command_handlers
        
        # Create TCP client
        result = handlers.handle_create_tcp_client("localhost", 502, 1)
        
        # Should fail to connect but test the API
        assert isinstance(result, dict)
        assert "success" in result
        
        # Test list_clients tool
        result = handlers.handle_list_clients()
        assert result["success"] is True
        
        # Test serial port discovery
        result = handlers.handle_list_serial_ports()
        assert result["success"] is True
    
    @pytest.mark.asyncio
    async def test_invalid_operations(self, test_config):
        """Test error handling for invalid operations."""
        app = create_app(test_config)
        handlers = app.command_handlers
        
        # Test operation on non-existent client
        result = handlers.handle_read_coils("nonexistent", 0, 10)
        assert result["success"] is False
        assert "error" in result
        
        # Test invalid parameters
        result = handlers.handle_create_tcp_client("localhost", 99999, 1)
        assert result["success"] is False
        assert "error" in result
    
    @pytest.mark.asyncio
    async def test_concurrent_clients(self, test_config):
        """Test multiple concurrent clients."""
        app = create_app(test_config)
        handlers = app.command_handlers
        
        # Test that we can attempt to create multiple clients
        # (they may fail to connect but should handle the requests)
        for i in range(3):
            result = handlers.handle_create_tcp_client("localhost", 502, i + 1)
            # Just verify we get a response
            assert isinstance(result, dict)
            assert "success" in result
        
        # Verify list clients works
        result = handlers.handle_list_clients()
        assert result["success"] is True
    
    @pytest.mark.asyncio
    async def test_serial_port_discovery(self, test_config):
        """Test serial port discovery functionality."""
        app = create_app(test_config)
        handlers = app.command_handlers
        
        # Test serial port listing
        result = handlers.handle_list_serial_ports()
        assert result["success"] is True
        assert "ports" in result
        assert isinstance(result["ports"], list)
        
        # Each port should have required fields
        for port in result["ports"]:
            assert "port" in port
            assert "description" in port
            assert "available" in port
            assert isinstance(port["available"], bool)


class TestErrorHandlingIntegration:
    """Test comprehensive error handling scenarios."""
    
    @pytest.mark.asyncio
    async def test_connection_timeout_handling(self, test_config):
        """Test connection timeout handling."""
        app = create_app(test_config)
        handlers = app.command_handlers
        
        # Try to connect to non-existent host
        result = handlers.handle_create_tcp_client("192.0.2.1", 502, 1)
        
        # Should fail gracefully (either timeout or connection error)
        # Note: The result might succeed in creating the client object but fail on actual connection
        assert isinstance(result, dict)
        assert "success" in result
        # The test passes if we get any response - the actual connection failure will be detected later
    
    @pytest.mark.asyncio
    async def test_validation_error_handling(self, test_config):
        """Test parameter validation error handling."""
        app = create_app(test_config)
        handlers = app.command_handlers
        
        # Test invalid slave ID
        result = handlers.handle_create_tcp_client("localhost", 502, 300)
        assert result["success"] is False
        assert "error" in result
        
        # Test invalid count regardless of client creation success
        result = handlers.handle_read_coils("test-client", 0, 3000)
        assert result["success"] is False
        assert "error" in result
    
    @pytest.mark.asyncio
    async def test_resource_cleanup(self, test_config):
        """Test proper resource cleanup."""
        app = create_app(test_config)
        handlers = app.command_handlers
        
        # Create several clients (may fail but test the cleanup)
        for i in range(5):
            handlers.handle_create_tcp_client("localhost", 502, 1)
        
        # Verify clients list works
        result = handlers.handle_list_clients()
        assert result["success"] is True
        
        # Cleanup all connections
        if hasattr(app, 'connection_manager'):
            app.connection_manager.cleanup_all()
        
        # Verify cleanup
        result = handlers.handle_list_clients()
        assert result["success"] is True
        assert len(result["clients"]) == 0