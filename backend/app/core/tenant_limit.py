"""Per-tenant cap on requests in progress, so one tenant can't take the whole server.

The app's regular (non-async) endpoints run on a shared pool of worker threads (AnyIO's default:
40). If one tenant's database hangs, its requests hold those threads while they wait, and with
no cap every other tenant queues behind them. Here at most `limit` requests per tenant are in
progress at once; the rest wait WITHOUT holding a thread and, after `wait_seconds`, get a 503
"busy" instead of waiting forever. A healthy tenant always finds free threads.

The tenant is resolved exactly as the endpoints resolve it (get_tenant_id_from_request: the
token's verified tenant, else the header, else the default). A slot is kept only while it is in
use, so made-up tenant names can't make this grow.
"""

import asyncio

from starlette.requests import Request
from starlette.responses import JSONResponse

from app.database.session import get_tenant_id_from_request

BUSY = "This organisation's server is busy right now - please try again in a moment."


class TenantConcurrencyLimit:
    def __init__(self, app, limit: int, wait_seconds: float):
        self.app = app
        self.limit = limit
        self.wait_seconds = wait_seconds
        self._slots: dict[str, list] = {}  # tenant -> [semaphore, requests holding or waiting]

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or self.limit <= 0:
            await self.app(scope, receive, send)
            return
        tenant = get_tenant_id_from_request(Request(scope))
        slot = self._slots.setdefault(tenant, [asyncio.Semaphore(self.limit), 0])
        slot[1] += 1
        try:
            try:
                await asyncio.wait_for(slot[0].acquire(), self.wait_seconds)
            except TimeoutError:
                await JSONResponse({"detail": BUSY}, status_code=503)(scope, receive, send)
                return
            try:
                await self.app(scope, receive, send)
            finally:
                slot[0].release()
        finally:
            slot[1] -= 1
            if slot[1] == 0 and self._slots.get(tenant) is slot:
                del self._slots[tenant]
