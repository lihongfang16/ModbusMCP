---
name: modbus-slave
description: |
  Modbus Slave (Server) full lifecycle and datastore management via MCP. Creates/stops RTU and TCP
  slave devices, reads/writes coils, discrete inputs, holding registers, and input registers in the
  slave's local datastore. Use when the user wants to: (1) Start a Modbus slave on serial or TCP,
  (2) Populate slave data for testing, (3) Simulate Modbus devices with coil/register values,
  (4) Read current slave datastore state. MCP server deployed on remote server (172.16.1.8:8090).
  Tools: create_rtu_server, create_tcp_server, stop_server, list_servers, server_read_coils,
  server_write_coils, server_read_discrete_inputs, server_write_discrete_inputs,
  server_read_holding_registers, server_write_holding_registers, server_read_input_registers,
  server_write_input_registers, server_set_alias, server_get_alias, server_list_aliases,
  server_get_register_log.
mcp:
  modbus-slave:
    type: sse
    url: "http://172.16.1.8:8090/sse"
---

# Modbus Slave

Full Modbus slave (server) management — lifecycle + coils + registers — via MCP.

**MCP server auto-starts via stdio** — no manual setup required. Uses `modbus-mcp-server --transport stdio`.

## Prerequisite

```bash
pip install modbus-mcp-server
```

---

## Lifecycle Tools

### create_rtu_server
Start a Modbus RTU slave on a serial port.

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `port` | str | *required* | Serial port (`"COM1"`, `"/dev/ttyUSB0"`) |
| `baudrate` | int | *required* | 9600, 19200, 38400, 57600, 115200 |
| `slave_id` | int | `1` | Slave ID (1-247) |

Returns `{success, server_id, message}`.

### create_tcp_server
Start a Modbus TCP slave on a network port.

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `host` | str | `"0.0.0.0"` | Bind IP |
| `port` | int | `502` | TCP port |
| `slave_id` | int | `1` | Slave ID (1-247) |

Returns `{success, server_id, message}`.

### stop_server(server_id: str)
Stop a running slave. Returns `{success, message}`.

### list_servers()
List all active slaves. Returns `{success, servers: [{server_id, server_type, connection_params, slave_id, running}]}`.

---

## Coil & Discrete Input Tools

### server_read_coils(server_id, address, count)
Read coil states. `address` 0-based, `count` 1-2000. Returns `{success, data: [bool, ...]}`.

### server_write_coils(server_id, address, values)
Set coil states. `values` = `[true, false, ...]`, max 1968. Returns `{success, message}`.

### server_read_discrete_inputs(server_id, address, count)
Read discrete input states. Same params as read_coils.

### server_write_discrete_inputs(server_id, address, values)
Pre-populate discrete inputs (normally read-only from client). Same params as write_coils.

---

## Register Tools

### server_read_holding_registers(server_id, address, count)
Read holding registers (analog outputs). `count` max 125. Returns `{success, data: [int, ...]}`.

### server_write_holding_registers(server_id, address, values)
Set holding registers. `values` = 16-bit ints (0-65535), max 123. Returns `{success, message}`.

### server_read_input_registers(server_id, address, count)
Read input registers (analog inputs). Same params as read_holding_registers.

### server_write_input_registers(server_id, address, values)
Pre-populate input registers (simulate sensor data). Same params as write_holding_registers.

---

## Usage Patterns

### Full RTU slave setup with sensor simulation

```
create_rtu_server("COM1", 9600, slave_id=1)
→ server_id: "rtu_COM1_9600_1"

server_write_holding_registers("rtu_COM1_9600_1", 0, [100, 200, 300])
server_write_coils("rtu_COM1_9600_1", 0, [true, false, true])
server_write_input_registers("rtu_COM1_9600_1", 0, [2500, 1800])

// Client connects to COM1@9600, sees holding regs [100,200,300],
// coils [ON,OFF,ON], input regs [2500,1800]
```

### TCP slave setup

```
create_tcp_server("0.0.0.0", 502, slave_id=1)
server_write_holding_registers("tcp_0.0.0.0_502_1", 0, [500, 600])
// Client connects to localhost:502 unit 1
```

### Read current state

```
list_servers()
server_read_holding_registers("rtu_COM1_9600_1", 0, 10)
server_read_coils("rtu_COM1_9600_1", 0, 10)
```

### Cleanup

```
stop_server("rtu_COM1_9600_1")
```

---

## Quick Reference

| Category | Tool | Access | Max per call |
|----------|------|--------|-------------|
| **Lifecycle** | `create_rtu_server` | — | — |
| | `create_tcp_server` | — | — |
| | `stop_server` | — | — |
| | `list_servers` | — | — |
| **Coils** | `server_read_coils` | R | 2000 |
| | `server_write_coils` | W | 1968 |
| **Discrete In** | `server_read_discrete_inputs` | R | 2000 |
| | `server_write_discrete_inputs` | W | 1968 |
| **Holding Reg** | `server_read_holding_registers` | R | 125 |
| | `server_write_holding_registers` | W | 123 |
| **Input Reg** | `server_read_input_registers` | R | 125 |
| | `server_write_input_registers` | W | 123 |

## Notes

- **Coils** = digital outputs (bool), **Discrete Inputs** = digital inputs (bool)
- **Holding Registers** = analog outputs/config (16-bit int), **Input Registers** = analog inputs/sensors (16-bit int)
- All addresses are 0-based (Modbus native)
- Slave ID range: 1-247
- Data is in-memory only — lost when server stops
- `server_write_discrete_inputs` and `server_write_input_registers` are server-side populate operations (normally read-only from client)
- Register values 0-65535; use scaling for real-world units (e.g., 250 = 25.0°C)
- Always `stop_server()` when done to free serial port / network port
