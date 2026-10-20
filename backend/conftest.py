"""pytest loads this file before it collects or imports any test module, so the test-suite safety
guard (tests/__init__.py) runs first: the app's settings can never be built from the real database
named in .env during a pytest run. `python run_tests.py` gets the same ordering from unittest's
discovery (see run_tests.py)."""

import tests  # noqa: F401 - importing the package applies the guard
