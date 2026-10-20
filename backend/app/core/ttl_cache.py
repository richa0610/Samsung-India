import threading
import time
from collections import OrderedDict
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
        # In the order stored (storing a key again moves it to the end), so the oldest entry - and
        # every expired one - is at the front: making room never scans the whole cache, which
        # matters for a large one (the login limiter's, core/rate_limit.py).
        self._items: OrderedDict[Hashable, tuple[float, Any]] = OrderedDict()
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
            if key in self._items:
                self._items.move_to_end(key)
            elif len(self._items) >= self._max:
                # Drop anything expired first, then the oldest entry if still full.
                while self._items and now - next(iter(self._items.values()))[0] >= self._ttl:
                    self._items.popitem(last=False)
                if len(self._items) >= self._max:
                    self._items.popitem(last=False)
            self._items[key] = (now, value)

    def discard(self, key: Hashable) -> None:
        """Forgets `key`, if it is kept."""
        with self._lock:
            self._items.pop(key, None)

    def clear(self) -> None:
        with self._lock:
            self._items.clear()

    def __len__(self) -> int:
        """How many entries are kept - an expired one counts until it is read or makes room."""
        with self._lock:
            return len(self._items)
