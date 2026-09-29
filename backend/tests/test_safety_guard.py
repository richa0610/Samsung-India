"""Proves the test suite cannot reach, initialise or alter a real database.

The checks that matter run in a fresh subprocess so they measure a clean import of
the app, independent of whatever other tests have already imported."""

import os
import subprocess
import sys
import textwrap
import unittest

from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

from app.core.config import settings

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Imports the app with a hook that records every database connection attempt and every
# statement, then prints the counts.
_PROBE = textwrap.dedent(
    """
    from sqlalchemy import event
    from sqlalchemy.engine import Engine

    attempts, statements = [], []

    @event.listens_for(Engine, "do_connect")
    def _connect(dialect, conn_rec, cargs, cparams):
        attempts.append((cparams.get("host"), cparams.get("port")))

    @event.listens_for(Engine, "before_cursor_execute")
    def _execute(conn, cursor, statement, params, context, executemany):
        statements.append(statement)

    import app.main  # noqa: F401
    print("ATTEMPTS", len(attempts), sorted(set(attempts)))
    print("STATEMENTS", len(statements))
    """
)


def _probe(env_overrides):
    env = dict(os.environ)
    env.update(env_overrides)
    result = subprocess.run(
        [sys.executable, "-c", _PROBE], cwd=BACKEND_DIR, env=env, capture_output=True, text=True, timeout=120
    )
    lines = {line.split(" ", 1)[0]: line for line in result.stdout.splitlines() if line.startswith(("ATTEMPTS", "STATEMENTS"))}
    return result, lines


class TestSuiteSafetyTests(unittest.TestCase):
    def test_settings_point_only_at_an_unusable_local_database(self):
        self.assertTrue(settings.TESTING)
        for host in (settings.DB_HOST, settings.common_db_host):
            self.assertEqual(host, "127.0.0.1")
        for port in (settings.DB_PORT, settings.common_db_port):
            self.assertEqual(port, 1)
        self.assertEqual(settings.DB_SSL_CA, "")

    def test_a_real_connection_attempt_is_refused(self):
        engine = create_engine(
            f"mysql+pymysql://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}",
            connect_args={"connect_timeout": 2},
        )
        with self.assertRaises(OperationalError):
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))

    def test_importing_the_app_under_testing_does_no_database_work(self):
        result, lines = _probe({})
        self.assertEqual(result.returncode, 0, result.stderr[-800:])
        self.assertTrue(lines["ATTEMPTS"].startswith("ATTEMPTS 0 "), lines)
        self.assertEqual(lines["STATEMENTS"], "STATEMENTS 0", lines)

    def test_negative_control_startup_does_try_to_initialise_when_not_testing(self):
        # Same unusable database, but TESTING switched off: the import-time
        # initialisation must now attempt to connect (and fail, harmlessly, on the
        # closed local port). This proves TESTING is what suppresses it, not luck.
        result, lines = _probe({"TESTING": "0"})
        self.assertEqual(result.returncode, 0, result.stderr[-800:])
        self.assertNotIn("ATTEMPTS 0 ", lines["ATTEMPTS"], lines)
        self.assertIn("127.0.0.1", lines["ATTEMPTS"])

    def test_settings_refuse_to_load_with_testing_and_a_remote_host(self):
        code = "from app.core.config import Settings; Settings()"
        env = dict(os.environ, TESTING="1", DB_HOST="db.example.com")
        result = subprocess.run([sys.executable, "-c", code], cwd=BACKEND_DIR, env=env, capture_output=True, text=True, timeout=60)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("refusing to start", result.stderr)


if __name__ == "__main__":
    unittest.main()
