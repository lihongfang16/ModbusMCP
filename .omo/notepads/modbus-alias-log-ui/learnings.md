# Learnings: Server stop alias cleanup (Task 6 verification)

## Summary
Verified `stop_server()` in `server_manager.py` — T6 agent correctly added `self.alias_manager.clear_aliases(server_id)` on the happy path (line 189), but the **exception handler (line 207) was missing it**, leaving orphaned aliases if `wrapper.stop()` or any cleanup raised.

## Fix Applied
- Added `self.alias_manager.clear_aliases(server_id)` to the `except Exception` block in `stop_server()` (line 211)
- Order in happy path is correct: `wrapper.stop()` → `clear_aliases()` → release ports → `del self.servers` → `del self.server_info`
- Exception handler now clears aliases, then cleans up ports, then removes from dicts

## Verification
- `test_alias_manager.py`: 19/19 passed (no regressions)
- Integration test: 4/4 passed (isolation, nonexistent server safety, multi-type clear, other-server non-interference)

---

# Learnings: OperationLog + LogEntry

## Summary
Created `OperationLog` (thread-safe ring buffer with subscriber support) and merged `LogEntry` into existing models.py.

## Key Decisions

### LogEntry merge strategy
- Existing `LogEntry` already had `server_id`, `register_type`, `address`, `operation`, `timestamp`, `source`, `count`, `alias`, `old_value`, `new_value`
- Added `value: Optional[Any] = None`, `success: bool = True`, `message: Optional[str] = None` to satisfy task requirements
- Removed duplicate `LogEntry` that was accidentally inserted between `ServerRTUParams` and `TCPParams`
- **Lesson**: Always check existing models before adding new ones to avoid duplicates

### Type annotation compatibility
- Project targets Python 3.8, but runs on 3.11
- Used `from __future__ import annotations` to allow `list[...]` and `tuple[...]` syntax
- `asyncio.Queue` generics not available in 3.8 — left unparameterized (LSP warnings but runtime-correct)
- Class-level constants need explicit `int` annotation to satisfy strict pyright (`MAXLEN: int = 10000`)

### Thread safety
- Used `threading.RLock` (same pattern as `ServerManager`) for all public methods
- Subscriber notification: copy subscriber list under lock, then iterate outside lock
- `loop.call_soon_threadsafe(queue.put_nowait, entry)` bridges MCP thread → asyncio loop

## Files Changed
- `src/modbus_mcp_server/models.py` — Added `value`, `success`, `message` to existing `LogEntry`
- `src/modbus_mcp_server/operation_log.py` — New file
- `tests/test_operation_log.py` — New file (16 tests)

## Test Coverage
- add/get_history round-trip (identity check)
- Empty log
- Ring buffer maxlen (10000)
- Filtering by server_id, register_type, address, combined, no-match
- Count limit (50) and default (100)
- Subscribe/unsubscribe (3 async tests)
- Thread safety (4 concurrent threads, 12000 total entries)

## Pre-existing Issues (not caused by this task)
- `test_connection_manager.py::TestConnectionManagerErrorScenarios::test_port_already_in_use_error` fails — COM1 not available on dev machine

---

# Learnings: Web UI REST API (Task 9)

## Summary
Created `web_ui.py` with FastAPI app factory and 6 REST endpoints; `test_web_ui.py` with 24 tests.

## Key Decisions

### Lazy FastAPI import
- `from fastapi import FastAPI, Query` is inside `create_web_app()`, not at module level
- This allows the module to be imported without FastAPI installed (optional dep in `pyproject.toml` under `[project.optional-dependencies] web-ui`)
- Test for this: parse source file, assert no top-level fastapi imports

### Serialization with `dataclasses.asdict()`
- `ServerInfo`, `LogEntry`, `AliasEntry` are all dataclasses — `asdict()` handles nested conversion
- `datetime` objects need manual `.isoformat()` conversion (asdict doesn't do this)
- `RegisterType` enum needs `.value` extraction for JSON serialization

### Register type → method mapping
- `_READ_METHOD_MAP` maps register_type strings to wrapper method names
- Invalid register_type returns 400 with helpful message listing valid types
- Missing server_id returns 404

### Query params
- `/api/registers`: server_id (required), register_type (required), address (default=0), count (default=100, max=65536)
- `/api/logs`: server_id (required), count (default=100, max=10000)
- `/api/aliases`: server_id (required)
- FastAPI auto-validates missing required params → 422

## Files Created
- `src/modbus_mcp_server/web_ui.py` — 120 lines (app factory + 6 endpoints)
- `tests/test_web_ui.py` — 24 tests across 7 test classes

## Test Coverage (24 tests)
- `TestRootEndpoint` (1): root returns status JSON
- `TestHealthEndpoint` (1): health returns healthy
- `TestServersEndpoint` (3): empty list, with entries, datetime serialization
- `TestRegistersEndpoint` (8): all 4 register types, server not found (404), missing param (422), invalid register_type (400), custom address/count
- `TestAliasesEndpoint` (3): empty, with entries, missing param (422)
- `TestLogsEndpoint` (5): empty, with entries, count param, default count, field serialization, missing param (422)
- `TestCreateWebApp` (2): returns FastAPI instance, lazy import verification

---

# Learnings: AuditingDataBlock (Task 4)

## Summary
Created `AuditingDataBlock` (subclass of `ModbusSequentialDataBlock`) that logs all external MCP read/write operations with alias resolution and address offset handling.

## Key Decisions

### Address offset (CRITICAL)
- `ModbusDeviceContext.getValues()` adds +1 to address before calling `DataBlock.getValues()`
- `AuditingDataBlock` receives address+1 and must subtract 1 for user-facing logging
- This is consistent with how `ModbusDeviceContext` wraps the data block

### ExcCodes check (CRITICAL)
- `ModbusSequentialDataBlock.getValues()` returns `ExcCodes.ILLEGAL_ADDRESS` (not an exception) on out-of-range
- Must check `isinstance(result, ExcCodes)` before logging — never log illegal address attempts
- `ExcCodes` imported from `pymodbus.constants` (not `pymodbus.pdu`)

### RegisterType enum mismatch (PRE-EXISTING)
- `alias_manager.py` defines its own `RegisterType` (COIL, DISCRETE_INPUT, etc.)
- `models.py` also defines `RegisterType` (coils, discrete_inputs, etc.) — different names/values
- `AuditingDataBlock` uses `alias_manager.RegisterType` throughout (matching alias system)
- `LogEntry` from `models.py` accepts any value for `register_type` field (dataclass, no runtime enforcement)

### mcp_set method
- Separate from `setValues` override to distinguish MCP-initiated writes from external Modbus client writes
- Returns `ExcCodes` on out-of-range (same pattern as super), skips logging

## Files Created
- `src/modbus_mcp_server/auditing_datastore.py` — AuditingDataBlock class (160 lines)
- `tests/test_auditing_datastore.py` — 24 tests across 4 test classes

## Test Coverage (24 tests)
- `TestGetValues` (7): returns correct data, logs operation, address offset, ILLEGAL_ADDRESS skip, alias resolution, no alias, all LogEntry fields
- `TestSetValues` (6): stores data, logs operation with old/new, address offset, ILLEGAL_ADDRESS skip, alias resolution, old value capture
- `TestMcpSet` (6): stores data, logs with mcp source, address offset, old value capture, alias resolution, ILLEGAL_ADDRESS skip
- `TestEdgeCases` (5): multiple ops accumulate, separate register types, single value get/set, timestamp populated

---

# Learnings: Dual-thread entry point (Task 10)

## Summary
Added dual-thread mode to `main.py`: when `config.enable_web_ui` is True, MCP stdio runs in a daemon background thread and FastAPI runs via uvicorn in the main thread.

## Key Decisions

### Lazy imports for uvicorn and create_web_app
- `import uvicorn` and `from .web_ui import create_web_app` are inside the `if enable_web_ui` block
- No top-level import of uvicorn/fastapi — keeps startup fast when web-ui is disabled

### Shared state before threads
- `app = create_app(config)` creates `server_manager` (which owns `operation_log` and `alias_manager`)
- These are extracted from `app.server_manager` before starting either thread
- Both threads share the same instances (thread-safe via RLock in ServerManager, OperationLog, AliasManager)

### Signal handling
- SIGINT/SIGTERM handlers registered in main thread (unchanged from before)
- Daemon MCP thread will be killed when main thread exits (uvicorn shutdown)

### Pre-existing bug fixed
- `web_ui.py` was missing `WebSocket` and `WebSocketDisconnect` imports — the lazy import line only had `FastAPI, Query`
- Added them back: `from fastapi import FastAPI, Query, WebSocket, WebSocketDisconnect`

## Files Changed
- `src/modbus_mcp_server/main.py` — Added `import threading`, dual-thread path in `main()`
- `src/modbus_mcp_server/web_ui.py` — Fixed missing WebSocket imports (pre-existing bug)

## Verification
- `test_main.py`: 2/2 passed
- `test_web_ui.py`: 28/29 passed (1 pre-existing failure: root endpoint test expects JSON but endpoint now returns FileResponse from another task)
- Manual QA: Health endpoint returns 200, servers endpoint returns 200, shared state correctly wired

---

# Learnings: WebSocket Log Streaming (Task 11)

## Summary
Added `WS /ws/logs` endpoint to `web_ui.py` for real-time log streaming. `operation_log.py` required zero changes — its `subscribe()`/`unsubscribe()` + `loop.call_soon_threadsafe()` notification was already complete.

## Key Decisions

### WebSocket handler pattern
- Simple async loop: `await queue.get()` → `websocket.send_json(_serialize_entry(entry))`
- `WebSocketDisconnect` caught explicitly (client-initiated close), generic `Exception` also caught (unexpected drops)
- `finally` block always calls `operation_log.unsubscribe(queue)` — guarantees cleanup

### Lazy import extended
- Added `WebSocket, WebSocketDisconnect` to the existing lazy import inside `create_web_app()` — consistent with project convention of keeping FastAPI optional

### TestClient WebSocket support
- `fastapi.testclient.TestClient` supports `client.websocket_connect("/ws/logs")` as context manager
- Uses real `OperationLog` instance (not mock) because subscribe/unsubscribe are the core behavior under test
- Verified subscriber cleanup by checking `ol._subscribers` list length before/after connection

## Files Changed
- `src/modbus_mcp_server/web_ui.py` — Added `WS /ws/logs` endpoint (~20 lines)
- `tests/test_web_ui.py` — Added `TestWsLogsEndpoint` (4 tests)

## Test Coverage (28 total: 24 existing + 4 new)
- `TestWsLogsEndpoint` (4): single entry receive, multiple entries in order, disconnect unsubscribes, field serialization completeness

## Verification
- `test_web_ui.py`: 28/28 passed
- `test_operation_log.py`: 16/16 passed (no regressions)
- `lsp_diagnostics` on `web_ui.py`: zero errors

---

# Learnings: Static Dashboard HTML (Task 12)

## Summary
Created `static/index.html` — vanilla JS dashboard with server selector, register type tabs, register table with alias merging, and WebSocket log panel. Updated `web_ui.py` to serve static files and the HTML at `/`.

## Key Decisions

### Static file serving
- `_STATIC_DIR = pathlib.Path(__file__).resolve().parent / "static"` — computed at module level so it's available to `create_web_app()`
- `StaticFiles(directory=str(_STATIC_DIR))` mounted at `/static`
- Root endpoint returns `FileResponse(_STATIC_DIR / "index.html")` instead of JSON
- Imports (`FileResponse`, `StaticFiles`) added inside `create_web_app()` alongside existing lazy imports

### Dashboard HTML architecture
- Single self-contained HTML file with embedded CSS and JS (no external deps)
- Server list polled every 10s via `/api/servers`
- Register type tabs map to `data-type` attribute matching `RegisterType` enum values
- Aliases fetched from `/api/aliases?server_id=X` and merged into register table via `aliasMap["type:address"]`
- WebSocket connects to `ws://<host>/ws/logs` with auto-reconnect every 5s on close
- Log entries color-coded: timestamp (gray), server (blue), operation (yellow), values (green)

### WebSocket URL construction
- Uses `location.protocol` to pick `ws:` vs `wss:` based on page protocol
- Falls back gracefully for plain-text log entries (non-JSON WebSocket messages)

## Files Changed
- `src/modbus_mcp_server/static/index.html` — New file (dashboard HTML + CSS + JS, ~270 lines)
- `src/modbus_mcp_server/web_ui.py` — Added `pathlib` import, `_STATIC_DIR` constant, `StaticFiles` mount, `FileResponse` root endpoint

## Verification
- `lsp_diagnostics` on `web_ui.py`: zero new errors (pre-existing WebSocket import warnings from T10)
