"""Configuration management for the Modbus MCP Server."""

import json
import os
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional, Union


@dataclass
class ServerConfig:
    """Server configuration settings."""
    
    # Server settings
    host: str = "localhost"
    port: int = 8000
    transport: str = "stdio"
    
    # Logging settings
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    log_file: Optional[str] = None
    
    # Connection settings
    default_timeout: float = 3.0
    max_clients: int = 100
    cleanup_interval: int = 300  # seconds
    
    # Modbus settings
    default_tcp_port: int = 502
    default_baudrate: int = 9600
    default_bytesize: int = 8
    default_parity: str = "N"
    default_stopbits: int = 1
    
    # Validation settings
    max_coil_count: int = 2000
    max_discrete_input_count: int = 2000
    max_holding_register_count: int = 125
    max_input_register_count: int = 125
    max_write_coil_count: int = 1968
    max_write_register_count: int = 123
    
    # Advanced settings
    enable_metrics: bool = False
    metrics_port: int = 9090
    enable_health_check: bool = True
    health_check_port: int = 8080


class ConfigManager:
    """Manages configuration loading from multiple sources."""
    
    def __init__(self, config_file: Optional[str] = None):
        """Initialize configuration manager.
        
        Args:
            config_file: Path to configuration file (optional)
        """
        self.config_file = config_file
        self.logger = logging.getLogger(__name__)
    
    def load_config(self) -> ServerConfig:
        """Load configuration from all sources.
        
        Configuration is loaded in the following order (later sources override earlier):
        1. Default values
        2. Configuration file
        3. Environment variables
        
        Returns:
            ServerConfig instance with loaded configuration
        """
        # Start with default configuration
        config = ServerConfig()
        
        # Load from configuration file if specified
        if self.config_file:
            file_config = self._load_from_file(self.config_file)
            if file_config:
                config = self._merge_config(config, file_config)
        
        # Override with environment variables
        env_config = self._load_from_env()
        config = self._merge_config(config, env_config)
        
        # Validate configuration
        self._validate_config(config)
        
        return config
    
    def _load_from_file(self, config_file: str) -> Optional[Dict[str, Any]]:
        """Load configuration from JSON file.
        
        Args:
            config_file: Path to configuration file
            
        Returns:
            Dictionary with configuration values or None if file not found
        """
        try:
            config_path = Path(config_file)
            if not config_path.exists():
                self.logger.warning(f"Configuration file not found: {config_file}")
                return None
            
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            self.logger.info(f"Loaded configuration from {config_file}")
            return config_data
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON in configuration file {config_file}: {e}")
            raise ValueError(f"Invalid JSON in configuration file: {e}")
        except Exception as e:
            self.logger.error(f"Error loading configuration file {config_file}: {e}")
            raise
    
    def _load_from_env(self) -> Dict[str, Any]:
        """Load configuration from environment variables.
        
        Environment variables should be prefixed with MODBUS_MCP_
        and use uppercase names with underscores.
        
        Returns:
            Dictionary with configuration values from environment
        """
        env_config = {}
        prefix = "MODBUS_MCP_"
        
        # Define environment variable mappings
        env_mappings = {
            f"{prefix}HOST": "host",
            f"{prefix}PORT": ("port", int),
            f"{prefix}TRANSPORT": "transport",
            f"{prefix}LOG_LEVEL": "log_level",
            f"{prefix}LOG_FORMAT": "log_format",
            f"{prefix}LOG_FILE": "log_file",
            f"{prefix}DEFAULT_TIMEOUT": ("default_timeout", float),
            f"{prefix}MAX_CLIENTS": ("max_clients", int),
            f"{prefix}CLEANUP_INTERVAL": ("cleanup_interval", int),
            f"{prefix}DEFAULT_TCP_PORT": ("default_tcp_port", int),
            f"{prefix}DEFAULT_BAUDRATE": ("default_baudrate", int),
            f"{prefix}DEFAULT_BYTESIZE": ("default_bytesize", int),
            f"{prefix}DEFAULT_PARITY": "default_parity",
            f"{prefix}DEFAULT_STOPBITS": ("default_stopbits", int),
            f"{prefix}MAX_COIL_COUNT": ("max_coil_count", int),
            f"{prefix}MAX_DISCRETE_INPUT_COUNT": ("max_discrete_input_count", int),
            f"{prefix}MAX_HOLDING_REGISTER_COUNT": ("max_holding_register_count", int),
            f"{prefix}MAX_INPUT_REGISTER_COUNT": ("max_input_register_count", int),
            f"{prefix}MAX_WRITE_COIL_COUNT": ("max_write_coil_count", int),
            f"{prefix}MAX_WRITE_REGISTER_COUNT": ("max_write_register_count", int),
            f"{prefix}ENABLE_METRICS": ("enable_metrics", lambda x: x.lower() in ('true', '1', 'yes')),
            f"{prefix}METRICS_PORT": ("metrics_port", int),
            f"{prefix}ENABLE_HEALTH_CHECK": ("enable_health_check", lambda x: x.lower() in ('true', '1', 'yes')),
            f"{prefix}HEALTH_CHECK_PORT": ("health_check_port", int),
        }
        
        for env_var, config_key in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                try:
                    if isinstance(config_key, tuple):
                        key, converter = config_key
                        env_config[key] = converter(value)
                    else:
                        env_config[config_key] = value
                except (ValueError, TypeError) as e:
                    self.logger.warning(f"Invalid value for {env_var}: {value} ({e})")
        
        if env_config:
            self.logger.info(f"Loaded {len(env_config)} configuration values from environment")
        
        return env_config
    
    def _merge_config(self, base_config: ServerConfig, override_config: Dict[str, Any]) -> ServerConfig:
        """Merge configuration dictionaries into ServerConfig.
        
        Args:
            base_config: Base ServerConfig instance
            override_config: Dictionary with override values
            
        Returns:
            New ServerConfig instance with merged values
        """
        # Convert base config to dictionary
        config_dict = base_config.__dict__.copy()
        
        # Update with override values
        for key, value in override_config.items():
            if hasattr(base_config, key):
                config_dict[key] = value
            else:
                self.logger.warning(f"Unknown configuration key: {key}")
        
        # Create new ServerConfig instance
        return ServerConfig(**config_dict)
    
    def _validate_config(self, config: ServerConfig) -> None:
        """Validate configuration values.
        
        Args:
            config: ServerConfig instance to validate
            
        Raises:
            ValueError: If configuration is invalid
        """
        # Validate port ranges
        if not (1 <= config.port <= 65535):
            raise ValueError(f"Invalid port: {config.port} (must be 1-65535)")
        
        if not (1 <= config.default_tcp_port <= 65535):
            raise ValueError(f"Invalid default TCP port: {config.default_tcp_port}")
        
        # Validate log level
        valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if config.log_level.upper() not in valid_log_levels:
            raise ValueError(f"Invalid log level: {config.log_level}")
        
        # Validate transport
        valid_transports = ["stdio", "sse", "websocket"]
        if config.transport not in valid_transports:
            raise ValueError(f"Invalid transport: {config.transport}")
        
        # Validate timeouts and limits
        if config.default_timeout <= 0:
            raise ValueError(f"Invalid timeout: {config.default_timeout}")
        
        if config.max_clients <= 0:
            raise ValueError(f"Invalid max clients: {config.max_clients}")
        
        # Validate Modbus limits
        if config.max_coil_count <= 0 or config.max_coil_count > 2000:
            raise ValueError(f"Invalid max coil count: {config.max_coil_count}")
        
        if config.max_holding_register_count <= 0 or config.max_holding_register_count > 125:
            raise ValueError(f"Invalid max holding register count: {config.max_holding_register_count}")
        
        # Validate serial settings
        valid_parities = ["N", "E", "O", "M", "S"]
        if config.default_parity not in valid_parities:
            raise ValueError(f"Invalid parity: {config.default_parity}")
        
        if config.default_bytesize not in [5, 6, 7, 8]:
            raise ValueError(f"Invalid bytesize: {config.default_bytesize}")
        
        if config.default_stopbits not in [1, 1.5, 2]:
            raise ValueError(f"Invalid stopbits: {config.default_stopbits}")
    
    def save_config(self, config: ServerConfig, output_file: str) -> None:
        """Save configuration to JSON file.
        
        Args:
            config: ServerConfig instance to save
            output_file: Path to output file
        """
        try:
            config_dict = config.__dict__.copy()
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(config_dict, f, indent=2, sort_keys=True)
            
            self.logger.info(f"Configuration saved to {output_file}")
            
        except Exception as e:
            self.logger.error(f"Error saving configuration to {output_file}: {e}")
            raise


def load_config(config_file: Optional[str] = None) -> ServerConfig:
    """Convenience function to load configuration.
    
    Args:
        config_file: Path to configuration file (optional)
        
    Returns:
        ServerConfig instance with loaded configuration
    """
    manager = ConfigManager(config_file)
    return manager.load_config()


def create_default_config_file(output_file: str) -> None:
    """Create a default configuration file.
    
    Args:
        output_file: Path to output configuration file
    """
    config = ServerConfig()
    manager = ConfigManager()
    manager.save_config(config, output_file)