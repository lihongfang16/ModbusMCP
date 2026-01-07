# Modbus MCP Server Usage Examples

This document provides practical examples of using the Modbus MCP Server with AI assistants in various scenarios.

## Basic Connection Examples

### Example 1: Discovering Serial Ports

**User:** "What serial ports are available on this system?"

**AI Response:** The AI will use the `list_serial_ports` tool and might respond:
```
I found the following serial ports on your system:
- COM1: Available (USB Serial Port)
- COM3: Available (Prolific USB-to-Serial Comm Port)
- COM4: In use by client 'rtu_client_001'
```

### Example 2: Creating RTU Connection

**User:** "Connect to a Modbus RTU device on COM3 with 9600 baud rate and slave ID 1"

**AI Response:** The AI will use `create_rtu_client` and respond:
```
Successfully connected to Modbus RTU device:
- Port: COM3
- Baud Rate: 9600
- Slave ID: 1
- Client ID: rtu_client_002

You can now perform read/write operations using this client.
```

### Example 3: Creating TCP Connection

**User:** "Connect to Modbus TCP device at 192.168.1.100 port 502 with slave ID 1"

**AI Response:** The AI will use `create_tcp_client` and respond:
```
Successfully connected to Modbus TCP device:
- Host: 192.168.1.100
- Port: 502
- Slave ID: 1
- Client ID: tcp_client_001

Connection established and ready for operations.
```

## Read Operation Examples

### Example 4: Reading Coils

**User:** "Read coils 1 through 16 from the connected RTU device"

**AI Response:** Using `read_coils`:
```
Coil values (addresses 1-16):
1: OFF, 2: ON, 3: OFF, 4: ON, 5: OFF, 6: OFF, 7: ON, 8: OFF,
9: ON, 10: ON, 11: OFF, 12: OFF, 13: ON, 14: OFF, 15: OFF, 16: ON

Summary: 6 coils are ON, 10 coils are OFF
```

### Example 5: Reading Holding Registers

**User:** "Read holding registers 40001 to 40010 and interpret them as temperature values"

**AI Response:** Using `read_holding_registers`:
```
Holding register values (40001-40010):
40001: 2350 (23.5°C)
40002: 2420 (24.2°C)
40003: 2380 (23.8°C)
40004: 2450 (24.5°C)
40005: 2390 (23.9°C)
40006: 2410 (24.1°C)
40007: 2370 (23.7°C)
40008: 2440 (24.4°C)
40009: 2360 (23.6°C)
40010: 2400 (24.0°C)

Average temperature: 24.0°C
```

### Example 6: Reading Input Registers

**User:** "Check the sensor readings from input registers 30001 to 30004"

**AI Response:** Using `read_input_registers`:
```
Input register values (sensor readings):
30001: 1250 (Pressure sensor: 12.5 PSI)
30002: 750 (Flow rate: 7.5 L/min)
30003: 2200 (Temperature: 22.0°C)
30004: 850 (Humidity: 85.0%)

All sensors are within normal operating ranges.
```

## Write Operation Examples

### Example 7: Writing Single Coil

**User:** "Turn ON coil 5 to start the conveyor motor"

**AI Response:** Using `write_coils`:
```
Successfully wrote to coil 5: ON
Conveyor motor has been started.

Current coil 5 status: ON
```

### Example 8: Writing Multiple Coils

**User:** "Set coils 1-4 to ON, OFF, ON, OFF respectively to configure the valve states"

**AI Response:** Using `write_coils`:
```
Successfully wrote to coils 1-4:
- Coil 1: ON (Inlet valve opened)
- Coil 2: OFF (Outlet valve closed)
- Coil 3: ON (Bypass valve opened)
- Coil 4: OFF (Drain valve closed)

Valve configuration updated successfully.
```

### Example 9: Writing Holding Registers

**User:** "Set the temperature setpoint to 25.5°C by writing 2550 to holding register 40001"

**AI Response:** Using `write_holding_registers`:
```
Successfully wrote 2550 to holding register 40001.
Temperature setpoint updated to 25.5°C.

The system will now maintain temperature at this new setpoint.
```

## Industrial Automation Examples

### Example 10: PLC Status Monitoring

**User:** "Connect to our main PLC at 192.168.1.50 and give me a status report"

**AI Workflow:**
1. Creates TCP connection to 192.168.1.50
2. Reads various registers and coils
3. Interprets the data based on PLC configuration

**AI Response:**
```
PLC Status Report (192.168.1.50):

System Status:
- Main power: ON (Coil 1)
- Emergency stop: NOT ACTIVE (Coil 2)
- Auto mode: ENABLED (Coil 3)
- Fault status: NO FAULTS (Coil 4)

Production Counters:
- Parts produced today: 1,247 (Register 40001-40002)
- Current cycle time: 45.2 seconds (Register 40003)
- Efficiency: 94.5% (Register 40004)

Temperature Monitoring:
- Zone 1: 23.5°C (Register 40010)
- Zone 2: 24.1°C (Register 40011)
- Zone 3: 23.8°C (Register 40012)

All systems operating normally.
```

### Example 11: Energy Management

**User:** "Monitor power consumption from our energy meter on COM1 and alert if usage exceeds 50kW"

**AI Workflow:**
1. Creates RTU connection to COM1
2. Reads power consumption registers
3. Sets up monitoring logic

**AI Response:**
```
Connected to energy meter on COM1.

Current Power Consumption:
- Phase 1: 15.2 kW (Register 30001)
- Phase 2: 14.8 kW (Register 30002)
- Phase 3: 16.1 kW (Register 30003)
- Total: 46.1 kW (Register 30004)

Status: NORMAL (Below 50kW threshold)

I'll continue monitoring and alert you if consumption exceeds 50kW.
```

### Example 12: HVAC System Control

**User:** "Check all temperature zones in our building and adjust setpoints if any are outside 22-26°C range"

**AI Workflow:**
1. Reads temperature values from multiple zones
2. Checks against acceptable range
3. Adjusts setpoints where needed

**AI Response:**
```
HVAC System Status Check:

Zone Temperatures:
- Zone 1 (Lobby): 24.2°C ✓ (Within range)
- Zone 2 (Office A): 27.1°C ⚠️ (Too high)
- Zone 3 (Office B): 23.5°C ✓ (Within range)
- Zone 4 (Conference): 21.8°C ⚠️ (Too low)
- Zone 5 (Storage): 25.1°C ✓ (Within range)

Adjustments Made:
- Zone 2: Setpoint reduced from 28°C to 25°C
- Zone 4: Setpoint increased from 20°C to 23°C

All zones should reach target temperatures within 30 minutes.
```

## Error Handling Examples

### Example 13: Connection Error

**User:** "Connect to device at 192.168.1.200"

**AI Response:**
```
Failed to connect to Modbus TCP device at 192.168.1.200:502

Error: Connection timeout after 3.0 seconds
Possible causes:
- Device is not reachable (check network connectivity)
- Device is not responding on port 502
- Firewall blocking connection
- Device is powered off or malfunctioning

Would you like me to try a different IP address or port?
```

### Example 14: Invalid Address Range

**User:** "Read 3000 coils starting from address 1"

**AI Response:**
```
Error: Invalid coil count requested

Details:
- Requested: 3000 coils
- Maximum allowed: 2000 coils per operation
- Modbus specification limit exceeded

Suggestion: Split the request into smaller chunks:
- Read coils 1-2000 first
- Then read coils 2001-3000 in a second operation

Would you like me to do this automatically?
```

### Example 15: Serial Port In Use

**User:** "Connect to RTU device on COM3"

**AI Response:**
```
Error: Cannot connect to COM3

Details:
- Port COM3 is already in use by client 'rtu_client_001'
- Connected to slave ID 2 since 14:30:25

Options:
1. Use the existing connection (if same slave ID)
2. Close existing connection and create new one
3. Try a different serial port

Available ports: COM1, COM4, COM5

Which option would you prefer?
```

## Advanced Usage Examples

### Example 16: Multi-Device Coordination

**User:** "Monitor temperature from sensor on COM1 and control heater via TCP device at 192.168.1.100 to maintain 25°C"

**AI Workflow:**
1. Creates RTU connection for temperature sensor
2. Creates TCP connection for heater controller
3. Implements control logic

**AI Response:**
```
Setting up temperature control system:

Temperature Sensor (COM1):
- Connected to RTU device, slave ID 1
- Reading from input register 30001
- Current temperature: 23.2°C

Heater Controller (192.168.1.100):
- Connected to TCP device, slave ID 1
- Control via holding register 40001
- Current setpoint: 20°C

Control Logic Activated:
- Target temperature: 25°C
- Current temperature: 23.2°C
- Action: Increasing heater setpoint to 27°C

I'll monitor and adjust every 30 seconds to maintain 25°C ±0.5°C.
```

### Example 17: Data Logging Setup

**User:** "Log data from all connected devices every minute and save to CSV file"

**AI Response:**
```
Data logging setup complete:

Connected Devices:
1. RTU Client (COM3) - Temperature sensors
2. TCP Client (192.168.1.100) - PLC status
3. TCP Client (192.168.1.101) - Energy meter

Data Points:
- Timestamp
- Temperature Zone 1-4 (RTU registers 30001-30004)
- Production counter (TCP registers 40001-40002)
- Power consumption (TCP registers 30001-30003)

Logging started: data_log_2024-01-15.csv
Interval: 60 seconds
Next log entry: 15:31:00

Data logging is now active. Use 'stop logging' to end.
```

## Troubleshooting Examples

### Example 18: Communication Issues

**User:** "I'm getting timeout errors when reading from my device"

**AI Response:**
```
Let me help diagnose the communication issues:

Current Connection:
- Type: Modbus RTU
- Port: COM3
- Baud rate: 9600
- Slave ID: 1
- Timeout: 3.0 seconds

Diagnostic Steps:
1. Testing basic connectivity... ✓ Port is accessible
2. Checking device response... ⚠️ Slow response detected
3. Verifying parameters... ⚠️ Baud rate mismatch suspected

Recommendations:
1. Try increasing timeout to 5 seconds
2. Verify device baud rate (common: 9600, 19200, 38400)
3. Check cable connections and length (<1200m for RS485)

Would you like me to try different baud rates automatically?
```

This comprehensive set of examples demonstrates the practical applications of the Modbus MCP Server across various industrial and automation scenarios.