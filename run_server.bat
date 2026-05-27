@echo off
REM Modbus MCP Server - Direct execution script
REM This script runs the server without requiring installation

echo Starting Modbus MCP Server...
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python 3.8+ and add it to your PATH
    pause
    exit /b 1
)

REM Check if required packages are installed
echo Checking dependencies...
python -c "import fastmcp, pymodbus, serial" >nul 2>&1
if errorlevel 1 (
    echo Installing required dependencies...
    python -m pip install fastmcp>=0.4.1 pymodbus==3.11.4 pyserial==3.5
    if errorlevel 1 (
        echo Error: Failed to install dependencies
        echo Please check your internet connection and pip installation
        pause
        exit /b 1
    )
)

echo Dependencies OK
echo.

REM Run the server
echo Running Modbus MCP Server...
python -m src.modbus_mcp_server.cli %*

if errorlevel 1 (
    echo.
    echo Server exited with error code %errorlevel%
    pause
)