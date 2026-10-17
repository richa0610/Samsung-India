"""Keeps bearer tokens out of the server's own log lines.

The WebSocket endpoints (routers/ws.py) take the token as a `?token=` query parameter - browsers
and React Native can't set an Authorization header on a WebSocket - and uvicorn logs every
WebSocket handshake with its full path and query string ('"WebSocket /ws/live/X?token=..."
[accepted]' / 403). Without this, every live connection wrote a replayable token into the log.

This only masks what this process logs; a reverse proxy in front of it keeps its own access
logs, which only moving the token out of the URL can fix."""

import logging
import re

_TOKEN_IN_QUERY = re.compile(r"(?i)([?&](?:access_)?token=)[^&\s\"']+")
REDACTED = "[REDACTED]"

# The loggers uvicorn writes request / handshake lines to.
_LOGGERS = ("uvicorn.error", "uvicorn.access")


def redact(text: str) -> str:
    return _TOKEN_IN_QUERY.sub(rf"\g<1>{REDACTED}", text)


class TokenRedactionFilter(logging.Filter):
    """Masks `token=` / `access_token=` query values in a record's message and arguments."""

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = redact(record.msg)
        if isinstance(record.args, tuple):
            record.args = tuple(redact(arg) if isinstance(arg, str) else arg for arg in record.args)
        elif isinstance(record.args, dict):
            record.args = {key: redact(value) if isinstance(value, str) else value for key, value in record.args.items()}
        return True


def install_token_redaction() -> None:
    """Idempotent: adds the filter to uvicorn's loggers once."""
    for name in _LOGGERS:
        logger = logging.getLogger(name)
        if not any(isinstance(existing, TokenRedactionFilter) for existing in logger.filters):
            logger.addFilter(TokenRedactionFilter())
