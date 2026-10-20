"""An open WebSocket holds no database connection (review finding, 2026-10-19).

The sign-in check runs on its own small worker pool - never on the event loop - and closes both
database sessions before the server says "ready"; only the company and username stay with the
socket. Before this, every open socket pinned a pooled connection for its whole life, so the 16th
signed-in trainer (or trainee in a Live Quiz) exhausted a company's pool and froze the server.

Synthetic TenantWorld (in-memory SQLite, plus one temporary file copy) only - no real database is
touched."""

import asyncio
import sqlite3
import tempfile
import threading
import time
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import patch

from sqlalchemy import create_engine, event
from sqlalchemy.exc import OperationalError
from sqlalchemy.pool import QueuePool
from starlette.websockets import WebSocketDisconnect

import app.routers.ws as ws_module
from app.core.security import create_access_token
from app.database.tenant import tenant_manager
from app.models.common.tenant_registry import Tenant
from app.models.trainee import Trainee
from tests.tenant_fixtures import ALPHA, uid
from tests.test_trainer_authorization import TrainerWorldTestCase

ADMIN_CHANNEL = "/ws/admin"
LIVE_ROOM = f"/ws/live/{uid('S_N1')}"  # trainer1's training; TR-S_N1-0 is on its roster


class SocketTestCase(TrainerWorldTestCase):
    def trainee_token(self):
        phone = self.alpha.query(Trainee).filter_by(traineeUid="TR-S_N1-0").one().phone
        return create_access_token(subject=str(phone), tenant_id=ALPHA, role="trainee")

    def open_ready(self, stack, path, token):
        """A socket opened inside `stack` that the server confirmed after the first-message auth."""
        socket = stack.enter_context(self.w.client.websocket_connect(path))
        socket.send_json({"type": "auth", "token": token})
        self.assertEqual(socket.receive_json(), {"type": "ready"})
        return socket

    def close_code(self, path, token):
        """The code the server closes a socket with after this sign-in."""
        with self.w.client.websocket_connect(path) as socket:
            socket.send_json({"type": "auth", "token": token})
            with self.assertRaises(WebSocketDisconnect) as refused:
                socket.receive_json()
        return refused.exception.code

    def use_file_database(self, pool_size, pool_timeout=0.5):
        """ALPHA's data copied into a file database behind a real QueuePool of `pool_size`
        connections. The in-memory world shares one StaticPool connection, which can never run out
        and can't be used by two threads at once - a real pool hands each check its own."""
        folder = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.addCleanup(folder.cleanup)
        path = Path(folder.name) / "alpha.db"
        source, copy = self.w.alpha_engine.raw_connection(), sqlite3.connect(path)
        try:
            source.driver_connection.backup(copy)
        finally:
            copy.close()
            source.close()
        engine = create_engine(f"sqlite:///{path}", poolclass=QueuePool, pool_size=pool_size, max_overflow=0,
                               pool_timeout=pool_timeout, connect_args={"check_same_thread": False})
        self.addCleanup(engine.dispose)
        tenant_manager.register_engine(ALPHA, engine)


class AnOpenSocketHoldsNoConnection(SocketTestCase):
    def setUp(self):
        super().setUp()
        self.held = {"tenant": 0, "common": 0}
        for name, engine in (("tenant", self.w.alpha_engine), ("common", self.w.common_engine)):
            def checkout(*_, name=name):
                self.held[name] += 1

            def checkin(*_, name=name):
                self.held[name] -= 1

            event.listen(engine, "checkout", checkout)
            event.listen(engine, "checkin", checkin)
            self.addCleanup(event.remove, engine, "checkout", checkout)
            self.addCleanup(event.remove, engine, "checkin", checkin)

    def test_a_signed_in_socket_keeps_no_connection_checked_out(self):
        cases = [
            ("trainer on the admin channel", ADMIN_CHANNEL, self.w.token("trainer1")),
            ("admin on the admin channel", ADMIN_CHANNEL, self.w.token("coadmin")),
            ("trainer in a live room", LIVE_ROOM, self.w.token("trainer1")),
            ("admin in a live room", LIVE_ROOM, self.w.token("coadmin")),
            ("trainee in a live room", LIVE_ROOM, self.trainee_token()),
        ]
        for label, path, token in cases:
            with self.subTest(label), ExitStack() as stack:
                before = dict(self.held)
                self.open_ready(stack, path, token)
                self.assertEqual(self.held, before, "a connection is still checked out while the socket is open")


class MoreSocketsThanThePoolHolds(SocketTestCase):
    POOL_SIZE = 2

    def setUp(self):
        super().setUp()
        self.use_file_database(self.POOL_SIZE)

    def test_every_socket_connects_and_requests_still_work(self):
        sockets = [(ADMIN_CHANNEL, self.w.token("trainer1")), (LIVE_ROOM, self.trainee_token())] * 3
        with ExitStack() as stack:
            for path, token in sockets:
                self.open_ready(stack, path, token)
            self.assertEqual(self.get("trainer1", "/admin/profile").status_code, 200)


class TheCheckRunsOffTheEventLoop(SocketTestCase):
    def test_the_database_lookup_never_runs_on_the_event_loop(self):
        where = []
        real = ws_module.resolve_principal

        def spy(*args, **kwargs):
            try:
                asyncio.get_running_loop()
                where.append("event loop")
            except RuntimeError:
                where.append("worker thread")
            return real(*args, **kwargs)

        with patch.object(ws_module, "resolve_principal", spy), ExitStack() as stack:
            self.open_ready(stack, ADMIN_CHANNEL, self.w.token("trainer1"))
            self.open_ready(stack, LIVE_ROOM, self.trainee_token())
        self.assertEqual(where, ["worker thread", "worker thread"])


class SignInChecksAreCapped(SocketTestCase):
    def test_a_burst_of_reconnects_runs_no_more_than_the_cap_at_once(self):
        cap = ws_module.HANDSHAKE_CONCURRENCY
        attempts = cap + 3
        token = self.w.token("trainer1")
        self.use_file_database(attempts)
        # One sign-in first, so the burst finds the tenant's status cached and doesn't read the
        # (single-connection, in-memory) common database from several threads at once.
        with ExitStack() as stack:
            self.open_ready(stack, ADMIN_CHANNEL, token)
        lock = threading.Lock()
        inside = {"now": 0, "most": 0}
        release = threading.Event()
        ready, errors = [], []
        real = ws_module.resolve_principal

        def held_open(*args, **kwargs):
            with lock:
                inside["now"] += 1
                inside["most"] = max(inside["most"], inside["now"])
            release.wait(5)
            try:
                return real(*args, **kwargs)
            finally:
                with lock:
                    inside["now"] -= 1

        def reconnect():
            try:
                with self.w.client.websocket_connect(ADMIN_CHANNEL) as socket:
                    socket.send_json({"type": "auth", "token": token})
                    if socket.receive_json() == {"type": "ready"}:
                        with lock:
                            ready.append(True)
            except Exception as exc:  # kept, so a failure shows in the assertion below
                with lock:
                    errors.append(exc)

        with patch.object(ws_module, "resolve_principal", held_open):
            threads = [threading.Thread(target=reconnect) for _ in range(attempts)]
            for thread in threads:
                thread.start()
            deadline = time.monotonic() + 5
            while inside["now"] < cap and time.monotonic() < deadline:
                time.sleep(0.01)
            time.sleep(0.3)  # room for a check over the cap to (wrongly) get in
            most_while_held = inside["most"]
            release.set()
            for thread in threads:
                thread.join(10)

        self.assertEqual(most_while_held, cap)
        self.assertEqual((len(ready), errors), (attempts, []))


class SignInFailuresCloseCleanly(SocketTestCase):
    def test_a_database_failure_closes_with_the_server_error_code(self):
        down = OperationalError("SELECT 1", {}, Exception("database is down"))
        with patch.object(ws_module, "resolve_principal", side_effect=down), self.assertLogs("ws", "ERROR"):
            self.assertEqual(self.close_code(ADMIN_CHANNEL, self.w.token("trainer1")), 1011)

    def test_a_refused_sign_in_still_closes_with_the_policy_code(self):
        cases = [
            ("not a token", ADMIN_CHANNEL, "not-a-jwt"),
            ("trainee on the admin channel", ADMIN_CHANNEL, self.trainee_token()),
            ("trainer outside their own room", f"/ws/live/{uid('S_S1')}", self.w.token("trainer1")),
            ("admin with no grant", ADMIN_CHANNEL, self.w.token("ungranted")),
        ]
        for label, path, token in cases:
            with self.subTest(label):
                self.assertEqual(self.close_code(path, token), 1008)

    def test_a_suspended_company_is_a_refusal_not_an_error(self):
        self.w.common.query(Tenant).filter_by(tenant_uid=ALPHA).update({"status": "suspended"})
        self.w.common.commit()
        tenant_manager.clear_status_cache()
        self.assertEqual(self.close_code(ADMIN_CHANNEL, self.w.token("trainer1")), 1008)
