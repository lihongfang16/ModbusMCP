"""FastAPI Web UI for the ModbusMCP dashboard.

Provides REST endpoints for inspecting servers, registers, aliases,
and operation logs. FastAPI is lazily imported to keep it as an
optional dependency.
"""

import pathlib
from dataclasses import asdict
from datetime import datetime
from typing import Any, Dict, List, Optional

from .models import RegisterType

_STATIC_DIR = pathlib.Path(__file__).resolve().parent / "static"


# Map register_type string to the corresponding wrapper read method name.
_READ_METHOD_MAP = {
    "coils": "read_coils",
    "discrete_inputs": "read_discrete_inputs",
    "holding_registers": "read_holding_registers",
    "input_registers": "read_input_registers",
}


def _serialize_entry(entry: Any) -> Dict[str, Any]:
    """Convert a dataclass instance to a JSON-safe dict."""
    d = asdict(entry)
    # Convert datetime objects to ISO strings.
    for key, value in d.items():
        if isinstance(value, datetime):
            d[key] = value.isoformat()
        elif isinstance(value, RegisterType):
            d[key] = value.value
    return d


def create_web_app(server_manager, operation_log, alias_manager):
    """Create and return a FastAPI application instance.

    FastAPI is imported inside this function so that the module can be
    loaded safely even when FastAPI is not installed (optional dep).

    Args:
        server_manager: ServerManager instance for server lookup.
        operation_log: OperationLog instance for log retrieval.
        alias_manager: AliasManager instance for alias listing.

    Returns:
        A configured FastAPI application.
    """
    # Lazy import — FastAPI is an optional dependency.
    from fastapi import FastAPI, Query, WebSocket, WebSocketDisconnect
    from fastapi.responses import FileResponse, JSONResponse
    from fastapi.staticfiles import StaticFiles

    app = FastAPI(title="ModbusMCP Web UI", docs_url=None, redoc_url=None)

    # Serve static assets (CSS, JS, images, etc.)
    app.mount("/static", StaticFiles(directory=str(_STATIC_DIR)), name="static")

    @app.get("/")
    def root():
        return FileResponse(_STATIC_DIR / "index.html")

    @app.get("/health")
    def health():
        return {"status": "healthy"}

    @app.get("/api/servers")
    def list_servers():
        servers = server_manager.list_servers()
        return [_serialize_entry(s) for s in servers]

    @app.get("/api/registers")
    def read_registers(
        server_id: str = Query(...),
        register_type: str = Query(...),
        address: int = Query(0, ge=0),
        count: int = Query(100, ge=1, le=65536),
    ):
        if register_type not in _READ_METHOD_MAP:
            return JSONResponse(
                status_code=400,
                content={"detail": f"Invalid register_type: {register_type}. Must be one of {list(_READ_METHOD_MAP.keys())}"},
            )

        wrapper = server_manager.servers.get(server_id)
        if wrapper is None:
            return JSONResponse(
                status_code=404,
                content={"detail": f"Server not found: {server_id}"},
            )

        method_name = _READ_METHOD_MAP[register_type]
        read_fn = getattr(wrapper, method_name)
        values = read_fn(address, count)
        return {"values": values}

    @app.get("/api/aliases")
    def list_aliases(server_id: str = Query(...)):
        aliases = alias_manager.list_aliases(server_id=server_id)
        return [_serialize_entry(a) for a in aliases]

    @app.get("/api/logs")
    def get_logs(
        server_id: str = Query(...),
        count: int = Query(100, ge=1, le=10000),
    ):
        entries = operation_log.get_history(server_id=server_id, count=count)
        return [_serialize_entry(e) for e in entries]

    # ── WebSocket: real-time log streaming ─────────────────────────────────

    @app.websocket("/ws/logs")
    async def ws_logs(websocket: WebSocket):
        """Stream new log entries to connected WebSocket clients.

        On connect the handler subscribes to *operation_log* and forwards
        every ``LogEntry`` as JSON.  When the client disconnects (or the
        connection drops) the subscription is automatically removed.
        """
        await websocket.accept()
        queue = operation_log.subscribe()
        try:
            while True:
                entry = await queue.get()
                await websocket.send_json(_serialize_entry(entry))
        except WebSocketDisconnect:
            pass
        except Exception:
            pass
        finally:
            operation_log.unsubscribe(queue)

    return app
