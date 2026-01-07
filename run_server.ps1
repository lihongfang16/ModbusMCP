# Modbus MCP Server - PowerShell execution script
# This script runs the server without requiring installation

Write-Host "Starting Modbus MCP Server..." -ForegroundColor Green
Write-Host ""

# Check if Python is available
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Found Python: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "Error: Python is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Python 3.8+ and add it to your PATH" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Check if required packages are installed
Write-Host "Checking dependencies..." -ForegroundColor Yellow
try {
    python -c "import fastmcp, pymodbus, serial" 2>$null
    Write-Host "Dependencies OK" -ForegroundColor Green
} catch {
    Write-Host "Installing required dependencies..." -ForegroundColor Yellow
    try {
        python -m pip install fastmcp>=0.2.0 pymodbus>=3.6.0 pyserial>=3.5
        Write-Host "Dependencies installed successfully" -ForegroundColor Green
    } catch {
        Write-Host "Error: Failed to install dependencies" -ForegroundColor Red
        Write-Host "Please check your internet connection and pip installation" -ForegroundColor Yellow
        Read-Host "Press Enter to exit"
        exit 1
    }
}

Write-Host ""

# Run the server
Write-Host "Running Modbus MCP Server..." -ForegroundColor Green
try {
    python -m src.modbus_mcp_server.cli $args
} catch {
    Write-Host ""
    Write-Host "Server exited with error" -ForegroundColor Red
    Read-Host "Press Enter to exit"
}