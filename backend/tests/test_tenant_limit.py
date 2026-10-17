"""app/core/tenant_limit.py: a tenant over its cap waits, then gets 503; others are unaffected."""

import asyncio
import unittest

from starlette.responses import JSONResponse

from app.core.tenant_limit import TenantConcurrencyLimit


def scope(tenant: str) -> dict:
    return {"type": "http", "method": "GET", "path": "/x", "headers": [(b"x-tenant-id", tenant.encode())], "query_string": b""}


class TenantLimit(unittest.TestCase):
    def run_requests(self, tenants, limit=2, wait=0.2, hold=0.5):
        async def slow_app(scope_, receive, send):
            await asyncio.sleep(hold)
            await JSONResponse({"ok": True})(scope_, receive, send)

        limiter = TenantConcurrencyLimit(slow_app, limit=limit, wait_seconds=wait)

        async def call(tenant):
            statuses = []

            async def send(message):
                if message["type"] == "http.response.start":
                    statuses.append(message["status"])

            async def receive():
                return {"type": "http.request", "body": b""}

            await limiter(scope(tenant), receive, send)
            return statuses[0]

        async def scenario():
            return await asyncio.gather(*(call(t) for t in tenants)), limiter._slots

        return asyncio.run(scenario())

    def test_over_the_cap_waits_then_gets_503_and_other_tenants_are_served(self):
        statuses, slots = self.run_requests(["SLOW"] * 4 + ["OK"])
        self.assertEqual(sorted(statuses[:4]), [200, 200, 503, 503])   # 2 served, 2 gave up waiting
        self.assertEqual(statuses[4], 200)                              # the other tenant never waited
        self.assertEqual(slots, {})                                     # nothing kept afterwards

    def test_waiting_requests_are_served_when_a_slot_frees_in_time(self):
        statuses, _ = self.run_requests(["T"] * 4, limit=2, wait=2.0, hold=0.2)
        self.assertEqual(statuses, [200, 200, 200, 200])

    def test_made_up_tenant_names_leave_nothing_behind(self):
        _, slots = self.run_requests([f"RANDOM{n}" for n in range(50)], limit=1, hold=0.01)
        self.assertEqual(slots, {})


if __name__ == "__main__":
    unittest.main()
