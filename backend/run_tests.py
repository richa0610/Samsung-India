"""Safe entry point for the backend test suite. Use this instead of a bare
`python -m unittest discover -s tests`.

Without an explicit top-level directory, unittest's discovery imports test
files as bare top-level modules (`test_x`) instead of through the `tests`
package (`tests.test_x`). That means `tests/__init__.py` - which forces
TESTING=1 and an unusable local database before anything can import
app.core.config - is only run whenever some test file happens to import a
sibling via `tests.something`, not deterministically before every test
file's own imports. Depending on unrelated import order between test files,
that race can silently construct the app's Settings singleton against the
real production database before the guard ever runs.

Passing top_level_dir explicitly makes every test file import through the
`tests.` package prefix, so `tests/__init__.py` always executes first,
deterministically - closing that race.
"""
import sys
import unittest
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent

if __name__ == "__main__":
    loader = unittest.TestLoader()
    suite = loader.discover(
        start_dir=str(BACKEND_DIR / "tests"),
        pattern="test_*.py",
        top_level_dir=str(BACKEND_DIR),
    )
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
