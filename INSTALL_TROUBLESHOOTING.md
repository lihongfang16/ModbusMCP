# Installation Troubleshooting Guide

## Error: "No module named pip"

This error typically occurs when pip is not properly installed or there are environment issues.

### Solution 1: Reinstall pip

```cmd
# Download get-pip.py
curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py

# Or if curl is not available, download manually from:
# https://bootstrap.pypa.io/get-pip.py

# Install pip
python get-pip.py

# Verify pip installation
python -m pip --version
```

### Solution 2: Use Python's built-in pip module

Instead of `pip install -e .`, try:

```cmd
python -m pip install -e .
```

### Solution 3: Install without development mode

```cmd
python -m pip install .
```

### Solution 4: Install dependencies manually

```cmd
# Install dependencies first
python -m pip install fastmcp>=0.2.0
python -m pip install pymodbus>=3.6.0
python -m pip install pyserial>=3.5

# Then install the package
python -m pip install .
```

### Solution 5: Use virtual environment (Recommended)

```cmd
# Create virtual environment
python -m venv modbus_env

# Activate virtual environment
# On Windows:
modbus_env\Scripts\activate
# On macOS/Linux:
source modbus_env/bin/activate

# Upgrade pip in virtual environment
python -m pip install --upgrade pip

# Install the package
python -m pip install -e .
```

### Solution 6: Alternative installation method

If all else fails, you can run the server directly without installation:

```cmd
# Install dependencies
python -m pip install fastmcp>=0.2.0 pymodbus>=3.6.0 pyserial>=3.5

# Run directly from source
python -m src.modbus_mcp_server.cli
```

## Quick Fix Commands

Try these commands in order until one works:

```cmd
# 1. Try with python -m pip
python -m pip install -e .

# 2. If that fails, try without -e flag
python -m pip install .

# 3. If that fails, install dependencies manually
python -m pip install fastmcp>=0.2.0 pymodbus>=3.6.0 pyserial>=3.5

# 4. Then try installing again
python -m pip install .
```

## Verification

After successful installation, verify with:

```cmd
# Check if the command is available
modbus-mcp-server --version

# Or run directly
python -m modbus_mcp_server.cli --version
```

## Common Issues on Windows

### Issue 1: Python not in PATH
Make sure Python is added to your system PATH during installation.

### Issue 2: Multiple Python versions
If you have multiple Python versions, specify the exact version:
```cmd
py -3.10 -m pip install -e .
```

### Issue 3: Permission issues
Run Command Prompt as Administrator if you get permission errors.

### Issue 4: Long path names
Windows has path length limitations. Try installing in a shorter path.

## Alternative: Direct execution without installation

If installation continues to fail, you can run the server directly:

1. Install dependencies:
```cmd
python -m pip install fastmcp>=0.2.0 pymodbus>=3.6.0 pyserial>=3.5
```

2. Create a batch file `run_modbus_server.bat`:
```batch
@echo off
cd /d "%~dp0"
python -m src.modbus_mcp_server.cli %*
```

3. Use the batch file instead of the installed command:
```cmd
run_modbus_server.bat --version
```

## Getting Help

If none of these solutions work:

1. Check your Python version: `python --version`
2. Check your pip version: `python -m pip --version`
3. Try creating a fresh virtual environment
4. Consider using conda instead of pip if available