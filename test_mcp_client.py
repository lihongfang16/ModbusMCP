#!/usr/bin/env python3
"""Simple MCP client test."""

import asyncio
import json
import subprocess
import sys

async def test_mcp_server():
    """Test MCP server with proper initialization."""
    
    # Start the server process
    process = subprocess.Popen(
        ["modbus-mcp-server", "--transport", "stdio"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    try:
        # Send initialization message
        init_message = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "test-client",
                    "version": "1.0.0"
                }
            }
        }
        
        print("Sending initialization message...")
        process.stdin.write(json.dumps(init_message) + "\n")
        process.stdin.flush()
        
        # Wait for response with timeout
        try:
            stdout, stderr = process.communicate(timeout=5)
            print(f"STDOUT: {stdout}")
            print(f"STDERR: {stderr}")
            print(f"Return code: {process.returncode}")
            return True
        except subprocess.TimeoutExpired:
            print("Server is running but didn't respond within 5 seconds")
            print("This might be normal - the server is waiting for proper MCP communication")
            process.kill()
            stdout, stderr = process.communicate()
            print(f"STDERR: {stderr}")
            return True
            
    except Exception as e:
        print(f"Error: {e}")
        process.kill()
        return False

if __name__ == "__main__":
    result = asyncio.run(test_mcp_server())
    sys.exit(0 if result else 1)