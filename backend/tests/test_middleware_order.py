"""The middleware chain in app/main.py: CORS is the outermost layer (SonarQube python:S8414).

Starlette runs middleware in the reverse order of add_middleware(), so CORS must be added last.
Then a browser's preflight is answered before the per-tenant request limit, and every response -
the limit's own 503 "busy" included - carries the CORS headers a browser needs to read it.
"""

import asyncio
import unittest
from unittest.mock import patch

from app.core.config import settings
from app.core.tenant_limit import TenantConcurrencyLimit
from tests.tenant_fixtures import ALPHA, TenantWorld


def middleware_layers(app) -> list:
    """The app's built middleware stack, outermost first (Starlette builds it on the first request)."""
    layer, layers = app.middleware_stack, []
    while layer is not app.router:
        layers.append(layer)
        layer = layer.app
    return layers


class CorsIsTheOutermostMiddleware(unittest.TestCase):
    def setUp(self):
        self.w = TenantWorld()
        self.addCleanup(self.w.close)
        self.w.client.get("/")  # builds the middleware stack
        self.origin = settings.allowed_origins_list[0]

    def test_cors_wraps_every_other_middleware(self):
        names = [type(layer).__name__ for layer in middleware_layers(self.w.app)]
        # ServerErrorMiddleware is Starlette's own last-resort layer, always outside the app's middleware.
        self.assertEqual(names[:3], ["ServerErrorMiddleware", "CORSMiddleware", "TenantConcurrencyLimit"])

    def test_a_preflight_is_answered_without_touching_the_tenant_limit(self):
        tenant_limit_reached = AssertionError("a preflight reached the tenant limit")
        with patch("app.core.tenant_limit.get_tenant_id_from_request", side_effect=tenant_limit_reached):
            response = self.w.client.options(
                "/admin/trainings/page",
                headers={
                    "Origin": self.origin,
                    "Access-Control-Request-Method": "GET",
                    "Access-Control-Request-Headers": "authorization",
                },
            )
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.headers.get("access-control-allow-origin"), self.origin)

    def test_the_tenant_limits_busy_response_carries_the_cors_headers(self):
        limiter = next(layer for layer in middleware_layers(self.w.app) if isinstance(layer, TenantConcurrencyLimit))
        every_slot_taken = [asyncio.Semaphore(0), 1]
        with patch.object(limiter, "wait_seconds", 0.05), patch.dict(limiter._slots, {ALPHA: every_slot_taken}):
            response = self.w.client.get(
                "/admin/trainings/page", headers={**self.w.headers("trainer1"), "Origin": self.origin}
            )
        self.assertEqual(response.status_code, 503, response.text)
        self.assertEqual(response.headers.get("access-control-allow-origin"), self.origin)

    def test_a_disallowed_origin_still_gets_no_cors_headers(self):
        response = self.w.client.get("/", headers={"Origin": "https://evil.example"})
        self.assertNotIn("access-control-allow-origin", response.headers)


if __name__ == "__main__":
    unittest.main()
