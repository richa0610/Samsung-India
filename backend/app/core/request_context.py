"""The request an audit column records (its method, path, caller IP, user agent and the login
token it carried), so the activity log (`activity_log_service.log_activity`) and the per-row audit
columns (attendance, results) can be filled for any action without every caller passing the
request down through the services.

Set once per HTTP request by RequestContextMiddleware; a context variable, so each request (and
the worker thread a regular endpoint runs on) sees only its own. Outside a request it is None.
"""

import hashlib
from contextvars import ContextVar
from dataclasses import dataclass

from starlette.requests import Request

from app.database.session import bearer_token, named_tenant
from app.utils.helpers import client_ip


@dataclass(frozen=True)
class RequestInfo:
    method: str
    path: str
    client_ip: str | None
    user_agent: str | None
    # The login token presented, if any - the log only ever stores a one-way fingerprint of it.
    token: str | None
    # The company (tenant) the request names - for the server's log lines (core/log_context.py).
    tenant: str | None = None

    @property
    def line(self) -> str:
        """The request as the `logPath` columns record it, e.g. "POST /attendance/check-in/secure"."""
        return f"{self.method} {self.path}"


_current: ContextVar[RequestInfo | None] = ContextVar("request_info", default=None)


def current_request() -> RequestInfo | None:
    return _current.get()


def token_fingerprint(token: str | None) -> str | None:
    """Tells one login session's actions apart from another's, but can't be turned back into the
    token or used to sign in - what a `token` audit column stores, never the token itself."""
    return f"sha256:{hashlib.sha256(token.encode()).hexdigest()[:16]}" if token else None


def request_trace() -> dict[str, str | None]:
    """How the current request changed a row, for its `token` (the login's fingerprint) and
    `logPath` (VARCHAR 100) columns. Empty outside a request, so a script leaves both as they were."""
    request = current_request()
    if request is None:
        return {}
    return {"token": token_fingerprint(request.token), "logPath": _fit(request.line, 100)}


def caller_device() -> dict[str, str | None]:
    """The current caller as the per-row audit columns of `attendance_logs` and
    `assessment_results` store it: `ipAddress` (VARCHAR 45) and `deviceInfo` (the user agent,
    VARCHAR 255), trimmed to fit rather than failing the insert. Both None outside a request."""
    request = current_request()
    if request is None:
        return {"ipAddress": None, "deviceInfo": None}
    return {"ipAddress": _fit(request.client_ip, 45), "deviceInfo": _fit(request.user_agent, 255)}


def _fit(value: str | None, limit: int) -> str | None:
    return value[:limit] if value else None


class RequestContextMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        request = Request(scope)
        reset = _current.set(
            RequestInfo(
                method=request.method,
                path=request.url.path,
                client_ip=client_ip(request),
                user_agent=request.headers.get("user-agent"),
                token=bearer_token(request),
                tenant=named_tenant(request),
            )
        )
        try:
            await self.app(scope, receive, send)
        finally:
            _current.reset(reset)
