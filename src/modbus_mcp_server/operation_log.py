"""Thread-safe ring buffer for Modbus operation logs with WebSocket subscriber support."""

from __future__ import annotations

import asyncio
import threading
from collections import deque
from typing import Optional

from .models import LogEntry, RegisterType


class OperationLog:
    """Thread-safe ring buffer for Modbus operation logs.

    Stores up to MAXLEN entries in a deque. Supports synchronous add/get_history
    with optional filtering, plus asyncio-based subscriber notification for
    real-time WebSocket push.

    Thread safety:
        All public methods acquire ``self._lock`` (``threading.RLock``) so they
        are safe to call from any thread. Subscriber notification uses
        ``loop.call_soon_threadsafe`` to bridge the MCP thread into the asyncio
        event loop.
    """

    MAXLEN: int = 10000
    """Maximum number of entries retained in the ring buffer."""

    DEFAULT_COUNT: int = 100
    """Default number of entries returned by ``get_history``."""

    def __init__(self) -> None:
        self._entries: deque[LogEntry] = deque(maxlen=self.MAXLEN)
        self._lock: threading.RLock = threading.RLock()
        self._subscribers: list[tuple[asyncio.Queue, asyncio.AbstractEventLoop]] = []

    # ── public API ─────────────────────────────────────────────────────────

    def add(self, entry: LogEntry) -> None:
        """Append a log entry and notify all subscribers.

        Args:
            entry: The log entry to record.
        """
        with self._lock:
            self._entries.append(entry)
            # Snapshot subscribers under the lock so iteration is safe.
            subscribers = list(self._subscribers)

        for queue, loop in subscribers:
            try:
                loop.call_soon_threadsafe(queue.put_nowait, entry)
            except Exception:
                pass  # Silently ignore disconnected subscribers.

    def get_history(
        self,
        server_id: Optional[str] = None,
        register_type: Optional[RegisterType] = None,
        address: Optional[int] = None,
        count: int = DEFAULT_COUNT,
    ) -> list[LogEntry]:
        """Return the most recent *count* entries that match the given filters.

        Filters are AND-ed together.  When a filter argument is ``None`` it
        is ignored (all entries pass).

        Args:
            server_id:   Only entries with this server ID.
            register_type: Only entries with this register type.
            address:     Only entries at this register address.
            count:       Maximum entries to return (default 100).

        Returns:
            A list of ``LogEntry`` objects, newest last (the natural deque
            order).  The list may be shorter than *count* if fewer entries match.
        """
        with self._lock:
            entries = list(self._entries)

        if server_id is not None:
            entries = [e for e in entries if e.server_id == server_id]
        if register_type is not None:
            entries = [e for e in entries if e.register_type == register_type]
        if address is not None:
            entries = [e for e in entries if e.address == address]

        return entries[-count:]

    def subscribe(self) -> asyncio.Queue:
        """Register a new subscriber and return its ``asyncio.Queue``.

        The caller (typically a WebSocket handler) must be inside a running
        asyncio event loop.  Every entry passed to :meth:`add` will be pushed
        onto the returned queue via ``loop.call_soon_threadsafe``.

        Returns:
            An ``asyncio.Queue`` that receives new ``LogEntry`` objects.
        """
        queue: asyncio.Queue = asyncio.Queue()
        loop = asyncio.get_running_loop()
        with self._lock:
            self._subscribers.append((queue, loop))
        return queue

    def unsubscribe(self, queue: asyncio.Queue) -> None:
        """Remove a previously registered subscriber queue.

        It is safe to call this with a queue that was never registered (no-op).

        Args:
            queue: The subscriber queue to remove.
        """
        with self._lock:
            self._subscribers = [
                (q, l) for q, l in self._subscribers if q is not queue
            ]
