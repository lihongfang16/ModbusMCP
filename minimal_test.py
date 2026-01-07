#!/usr/bin/env python3
"""Minimal FastMCP test."""

from fastmcp import FastMCP
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)

app = FastMCP("test-server")

@app.tool()
def hello() -> str:
    """Say hello."""
    return "Hello, World!"

if __name__ == "__main__":
    print("Starting minimal FastMCP server...")
    try:
        app.run(transport="stdio")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()