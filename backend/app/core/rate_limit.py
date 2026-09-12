import time
from collections import defaultdict

from fastapi import HTTPException, Request, status

# Single-process, in-memory fixed-window counters keyed by "path:client_ip".
# Fine for a dev/prototype deployment; if this ever runs behind multiple
# worker processes, move the counters to Redis instead.
_attempts: dict[str, list[float]] = defaultdict(list)


def _client_ip(request: Request) -> str:
    # Behind the Cloudflare tunnel, request.client.host is always 127.0.0.1,
    # which would rate-limit every user as one. Cloudflare sets
    # CF-Connecting-IP with the real caller; X-Forwarded-For is the generic
    # fallback for any other reverse proxy. Only trust these because this
    # API is never reached directly - always through the tunnel/proxy.
    cf_ip = request.headers.get("cf-connecting-ip")
    if cf_ip:
        return cf_ip.strip()
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def rate_limit(max_attempts: int = 5, window_seconds: int = 300):
    def dependency(request: Request) -> None:
        key = f"{request.url.path}:{_client_ip(request)}"
        now = time.monotonic()
        window_start = now - window_seconds

        attempts = _attempts[key]
        attempts[:] = [t for t in attempts if t > window_start]

        if len(attempts) >= max_attempts:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many attempts. Please try again later.",
            )

        attempts.append(now)

    return dependency
