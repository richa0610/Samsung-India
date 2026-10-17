"""Marks a test that describes behaviour a LATER Phase C step will introduce.

Until that step lands the test is `expectedFailure`, so the suite stays green while the test still
runs and documents the target. When the step is implemented the test starts passing, unittest
reports an "unexpected success", and the decorator is removed - a built-in reminder.

Run the whole set for real (to see exactly how each one fails today, or to check it after a step):

    PHASE_C_ENFORCE=1 python -m unittest tests.test_tenant_isolation
"""

import os
import unittest


def pending_phase_c(step: str):
    def decorate(test):
        test.phase_c_step = step
        if os.environ.get("PHASE_C_ENFORCE") == "1":
            return test
        return unittest.expectedFailure(test)

    return decorate
