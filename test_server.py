#!/usr/bin/env python3
"""Simple test to check if the server can start."""

import asyncio
import sys
from src.modbus_mcp_server.main import create_app
from src.modbus_mcp_server.config import load_config

async def test_server():
    """Test if the server can be created and initialized."""
    try:
        config = load_config()
        app = create_app(config)
        print("✓ Server created successfully")
        print(f"✓ Config loaded: transport={config.transport}")
        print("✓ App initialized")
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_server())
    sys.exit(0 if result else 1)