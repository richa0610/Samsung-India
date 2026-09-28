import threading
import time
from typing import Any, Hashable, Optional


class TTLCache:
    """Tiny in-process cache: each entry expires `ttl_seconds` after it was
    stored, and at most `max_entries` are kept (the oldest is dropped first).

    In-memory and per process, like the rate limiter (see core/rate_limit.py) -
    fine for the current single worker; with several workers each would keep its
    own copy, and this should move to a shared store such as Redis."""

    def __init__(self, ttl_seconds: float, max_entries: int = 500) -> None:
        self._ttl = ttl_seconds
        self._max = max_entries
        self._items: dict[Hashable, tuple[float, Any]] = {}
        self._lock = threading.Lock()

    def get(self, key: Hashable) -> Optional[Any]:
        with self._lock:
            entry = self._items.get(key)
            if entry is None:
                return None
            stored_at, value = entry
            if time.monotonic() - stored_at >= self._ttl:
                del self._items[key]
                return None
            return value

    def set(self, key: Hashable, value: Any) -> None:
        with self._lock:
            now = time.monotonic()
            if key not in self._items and len(self._items) >= self._max:
                # Drop anything expired first, then the oldest entry if still full.
                for stale in [k for k, (t, _) in self._items.items() if now - t >= self._ttl]:
                    del self._items[stale]
                if len(self._items) >= self._max:
                    del self._items[min(self._items, key=lambda k: self._items[k][0])]
            self._items[key] = (now, value)

    def clear(self) -> None:
        with self._lock:
            self._items.clear()
