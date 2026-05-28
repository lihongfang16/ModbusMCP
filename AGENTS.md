# ModbusMCP Project Knowledge Base

**Scope:** ModbusMCP — Modbus MCP Server with Alias, Logging & Web UI

## OVERVIEW

ModbusMCP is a Python FastMCP server providing Modbus RTU/TCP client and slave (server) operations via MCP protocol. Forked from alejoseb/ModbusMCP, enhanced with alias system, operation logging, and Web UI dashboard.

**Core Stack:** Python 3.10+, FastMCP, pymodbus 3.11.4, FastAPI (optional Web UI)

## STRUCTURE

```
ModbusMCP/
├── src/modbus_mcp_server/     # Main package
│   ├── main.py                 # Entry point, FastMCP app, dual-thread
│   ├── cli.py                  # CLI argument parsing
│   ├── config.py               # ServerConfig dataclass
│   ├── command_handlers.py     # Client-side MCP tools (11)
│   ├── server_command_handlers.py  # Server-side MCP tools (16)
│   ├── connection_manager.py   # Client connection lifecycle
│   ├── client_wrapper.py       # pymodbus client wrapper
│   ├── server_manager.py       # Server (slave) lifecycle
│   ├── server_wrapper.py       # pymodbus server wrapper + datastore
│   ├── alias_manager.py        # Register alias management
│   ├── operation_log.py        # Ring buffer + WebSocket subscribers
│   ├── auditing_datastore.py   # pymodbus DataBlock subclass
│   ├── web_ui.py               # FastAPI app + REST + WebSocket
│   ├── models.py               # Data models (RegisterType, LogEntry)
│   └── validation.py           # ModbusValidator
├── tests/                      # Test suite (192 tests)
├── skills/modbus-slave/        # OpenCode skill with MCP config
│   ├── SKILL.md                # Skill definition
│   └── mcp.json                # MCP server config (SSE)
├── examples/                   # Usage examples
├── pyproject.toml              # Package config + [web-ui] extras
└── README.md                   # Documentation
```

## WHERE TO LOOK

| Task | Location | Notes |
|------|----------|-------|
| MCP tool handlers (client) | `command_handlers.py` | 11 client tools |
| MCP tool handlers (server) | `server_command_handlers.py` | 16 server tools |
| Alias system | `alias_manager.py` | Per-server register aliases |
| Operation logging | `operation_log.py` | Deque ring buffer, WebSocket push |
| External read/write intercept | `auditing_datastore.py` | ModbusSequentialDataBlock subclass |
| Web UI | `web_ui.py` + `static/index.html` | FastAPI + real-time log stream |
| Dual-thread entry | `main.py` | MCP stdio daemon + FastAPI main |
| Skill config | `skills/modbus-slave/` | MCP SSE config pointing to remote server |

## CONVENTIONS

- Chinese comments, English identifiers
- Each server independent directory, own `requirements.txt`
- Entry files: `main.py` or `server.py`
- Transport: default `stdio`, switchable via env
- Auth: Bearer Token via environment variables

## ANTI-PATTERNS

- `as any` / `@ts-ignore` — NEVER
- Empty catch blocks — NEVER
- Hardcoded values — ALWAYS externalize to config
- Modifying pymodbus source — FORBIDDEN

## COMMANDS

```bash
# Install with Web UI
pip install -e ".[web-ui]"

# Start with Web UI
python -m modbus_mcp_server --web-ui --web-ui-port 8090

# Start stdio only (default)
python -m modbus_mcp_server

# Run tests
python -m pytest tests/ --ignore=tests/test_connection_manager.py
```

## DEPLOYMENT

- **Remote Server:** `<your-server-ip>:8090`
- **Service:** `systemctl status modbus-mcp`
- **Auto-start:** `enabled` via systemd

## NOTES

- **Fork:** 基于 alejoseb/ModbusMCP 的增强版本
- **Upstream:** `https://github.com/alejoseb/ModbusMCP`
- **Web UI:** Vanilla JS, no frameworks, terminal-style log panel
- **Threading:** MCP stdio in daemon thread, FastAPI in main thread
- **Log buffer:** 10000 entries max, in-memory only
- **Alias scope:** per (server_id, register_type, address)
- **Address offset:** pymodbus +1 internally, logged as user-facing address
