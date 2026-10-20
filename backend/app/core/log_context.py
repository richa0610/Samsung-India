"""Every server log line names the company (tenant) it is about (user, 2026-10-19), e.g.

    INFO:     [samsung] 10.0.0.5:51234 - "GET /sessions/current HTTP/1.1" 200 OK
    WARNING:  [demo] tenant_manager: Failed to re-check tenant status for 'demo'

so a line on Render can be traced to its company without guessing. The tenant is the one the request
names - its verified token's, else the company code it sent (request_context / session.named_tenant) -
and "-" outside a request (startup, the keep-alive pings, a WebSocket) or when a request names none.

uvicorn sets up its log handlers before it imports the app, so `install_tenant_log_tags` (called from
main.py) finds them in place; a custom --log-config keeps its own formats, which may print %(tenant)s."""

import logging
import sys

from uvicorn.logging import AccessFormatter, DefaultFormatter

from app.core.request_context import current_request

NO_TENANT = "-"
# uvicorn's own formats (uvicorn.config.LOGGING_CONFIG) with the tenant in front.
DEFAULT_FORMAT = "%(levelprefix)s [%(tenant)s] %(message)s"
ACCESS_FORMAT = '%(levelprefix)s [%(tenant)s] %(client_addr)s - "%(request_line)s" %(status_code)s'
# The app's own loggers (tenant_manager, tenant_session, ...) also name themselves.
APP_FORMAT = "%(levelprefix)s [%(tenant)s] %(name)s: %(message)s"

# The loggers uvicorn attaches its handlers to ("uvicorn.error" writes through "uvicorn"'s).
_UVICORN_LOGGERS = ("uvicorn", "uvicorn.access")


class TenantLogFilter(logging.Filter):
    """Gives every record a `tenant`, which the formats above print."""

    def filter(self, record: logging.LogRecord) -> bool:
        request = current_request()
        record.tenant = (request.tenant if request else None) or NO_TENANT
        return True


def _with_tenant(formatter: logging.Formatter | None) -> logging.Formatter | None:
    """uvicorn's own formatter, unchanged but for the tenant; any other one is kept as it is."""
    colours = getattr(formatter, "use_colors", None)
    if isinstance(formatter, AccessFormatter):
        return AccessFormatter(ACCESS_FORMAT, use_colors=colours)
    if isinstance(formatter, DefaultFormatter):
        return DefaultFormatter(DEFAULT_FORMAT, use_colors=colours)
    return formatter


def tag_handler(handler: logging.Handler) -> None:
    """Idempotent: the tenant filter on `handler`, and the tenant in its format."""
    if not any(isinstance(existing, TenantLogFilter) for existing in handler.filters):
        handler.addFilter(TenantLogFilter())
    handler.setFormatter(_with_tenant(handler.formatter))


def install_tenant_log_tags() -> None:
    """Idempotent: uvicorn's server and request lines, and - through a handler on the root logger,
    which has none under uvicorn - the app's own warnings and errors."""
    for name in _UVICORN_LOGGERS:
        for handler in logging.getLogger(name).handlers:
            tag_handler(handler)
    root = logging.getLogger()
    if not root.handlers:
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(DefaultFormatter(APP_FORMAT))
        handler.addFilter(TenantLogFilter())
        root.addHandler(handler)
