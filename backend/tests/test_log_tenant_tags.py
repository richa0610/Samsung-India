"""app/core/log_context.py - every server log line names its company (user, 2026-10-19): the tenant
the request names (its verified token's, else the company code it sent), "-" outside a request or
when a request names none. uvicorn's request and server lines carry it, in uvicorn's own format."""

import io
import logging
import unittest

from starlette.testclient import TestClient
from uvicorn.logging import AccessFormatter, DefaultFormatter

from app.core.log_context import ACCESS_FORMAT, DEFAULT_FORMAT, TenantLogFilter, install_tenant_log_tags, tag_handler
from app.core.request_context import RequestContextMiddleware
from app.core.security import create_access_token


def logging_app(emit):
    """A bare ASGI app behind the request context that logs one line while serving a request."""

    async def app(scope, receive, send):
        emit()
        await send({"type": "http.response.start", "status": 200, "headers": []})
        await send({"type": "http.response.body", "body": b""})

    return RequestContextMiddleware(app)


class TenantOnLogLines(unittest.TestCase):
    def logger(self, name, formatter):
        stream = io.StringIO()
        handler = logging.StreamHandler(stream)
        handler.setFormatter(formatter)
        tag_handler(handler)
        logger = logging.getLogger(name)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False
        self.addCleanup(logger.removeHandler, handler)
        return logger, stream

    def serve(self, emit, headers):
        TestClient(logging_app(emit)).get("/x", headers=headers)

    def setUp(self):
        self.log, self.stream = self.logger("tests.tenant_tags", DefaultFormatter("%(levelprefix)s %(message)s", use_colors=False))

    def test_a_request_is_tagged_with_the_company_code_it_sent(self):
        self.serve(lambda: self.log.warning("inside"), {"X-Tenant-ID": " samsung "})
        self.assertIn("[samsung] inside", self.stream.getvalue())

    def test_a_signed_in_request_is_tagged_with_its_tokens_company_whatever_header_it_sends(self):
        token = create_access_token("9000000001", "demo")
        self.serve(lambda: self.log.warning("inside"), {"Authorization": f"Bearer {token}", "X-Tenant-ID": "samsung"})
        self.assertIn("[demo] inside", self.stream.getvalue())

    def test_no_company_and_outside_a_request_is_a_dash(self):
        self.serve(lambda: self.log.warning("inside"), {})
        self.log.warning("startup")
        self.assertEqual(self.stream.getvalue().split("\n")[:2], ["WARNING:  [-] inside", "WARNING:  [-] startup"])

    def test_uvicorns_request_lines_carry_it_in_uvicorns_own_format(self):
        access, stream = self.logger("tests.tenant_tags.access", AccessFormatter(use_colors=False))
        emit = lambda: access.info('%s - "%s %s HTTP/%s" %d', "10.0.0.5:51234", "GET", "/x", "1.1", 200)
        self.serve(emit, {"X-Tenant-ID": "samsung"})
        self.assertEqual(stream.getvalue().strip(), 'INFO:     [samsung] 10.0.0.5:51234 - "GET /x HTTP/1.1" 200 OK')

    def test_installing_again_tags_uvicorns_handlers_once(self):
        handlers = {"uvicorn": DefaultFormatter(use_colors=False), "uvicorn.access": AccessFormatter(use_colors=False)}
        for name, formatter in handlers.items():
            handler = logging.StreamHandler(io.StringIO())
            handler.setFormatter(formatter)
            logging.getLogger(name).addHandler(handler)
            self.addCleanup(logging.getLogger(name).removeHandler, handler)
            handlers[name] = handler
        install_tenant_log_tags()
        install_tenant_log_tags()
        for name, expected in (("uvicorn", DEFAULT_FORMAT), ("uvicorn.access", ACCESS_FORMAT)):
            with self.subTest(logger=name):
                handler = handlers[name]
                self.assertEqual(sum(isinstance(f, TenantLogFilter) for f in handler.filters), 1)
                self.assertEqual(handler.formatter._fmt, expected)

    def test_a_custom_format_is_kept(self):
        handler = logging.StreamHandler(io.StringIO())
        custom = logging.Formatter("%(message)s")
        handler.setFormatter(custom)
        tag_handler(handler)
        self.assertIs(handler.formatter, custom)


if __name__ == "__main__":
    unittest.main()
