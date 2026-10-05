"""Safety layer for the performance harness. Import this FIRST, before any `app` module.

The harness must never reach, initialise or alter a real database, so:
  1. Every setting the app reads at import time is forced (environment variables beat
     `.env`) to an unusable local address with TESTING=1, exactly like tests/__init__.py.
     Importing app modules therefore does no database work and never sees real credentials.
  2. The only database the harness talks to is the one in PERF_DB_URL (never `.env`), and
     `perf_engine` refuses it unless the host is loopback AND the database name starts
     with "perf_". `.env` is never read.
"""

import os

os.environ.update(
    {
        "TESTING": "1",
        "DB_HOST": "127.0.0.1",
        "DB_PORT": "1",
        "DB_USER": "test",
        "DB_PASSWORD": "test",
        "DB_NAME": "test",
        "DB_SSL_CA": "",
        "COMMON_DB_HOST": "127.0.0.1",
        "COMMON_DB_PORT": "1",
        "COMMON_DB_USER": "test",
        "COMMON_DB_PASSWORD": "test",
        "COMMON_DB_NAME": "test",
        "SECRET_KEY": "perf-harness-not-a-secret",
        "ALGORITHM": "HS256",
        "ACCESS_TOKEN_EXPIRE_MINUTES": "30",
    }
)

from sqlalchemy import create_engine, text  # noqa: E402
from sqlalchemy.engine import URL, make_url  # noqa: E402

_LOOPBACK = ("127.0.0.1", "localhost", "::1")


def _base_url() -> URL:
    raw = os.environ.get("PERF_DB_URL")
    if not raw:
        raise SystemExit("PERF_DB_URL is not set (it must point at the local perf MySQL container).")
    url = make_url(raw)
    if url.host not in _LOOPBACK:
        raise SystemExit("Refusing to run: PERF_DB_URL host is not loopback.")
    return url


def _checked_name(name: str) -> str:
    if not name.startswith("perf_") or not name.replace("_", "").isalnum():
        raise SystemExit(f"Refusing database name {name!r}: it must start with 'perf_'.")
    return name


def server_engine():
    """Connection to the server itself (no database selected) - used only to create /
    drop `perf_*` databases."""
    base = _base_url()
    # URL.set(database=None) would mean "unchanged", so build the URL without a database explicitly.
    server_url = URL.create(base.drivername, base.username, base.password, base.host, base.port, None, dict(base.query))
    return create_engine(server_url, isolation_level="AUTOCOMMIT")


def ensure_database(name: str, drop_first: bool = False) -> None:
    name = _checked_name(name)
    with server_engine().connect() as conn:
        if drop_first:
            conn.execute(text(f"DROP DATABASE IF EXISTS `{name}`"))
        conn.execute(text(f"CREATE DATABASE IF NOT EXISTS `{name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci"))


def perf_engine(name: str, **kwargs):
    name = _checked_name(name)
    return create_engine(_base_url().set(database=name), pool_pre_ping=True, **kwargs)
