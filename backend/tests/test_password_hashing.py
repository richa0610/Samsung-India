"""BCRYPT_ROUNDS (core/config.py): new password hashes use the configured cost, existing hashes keep
verifying whatever cost they were made with, and the setting can't be pushed outside 10..14."""

import unittest
from unittest.mock import patch

import bcrypt
from pydantic import ValidationError

from app.core.config import Settings, settings
from app.core.security import hash_password, verify_password


class PasswordHashing(unittest.TestCase):
    def test_new_hashes_use_the_configured_cost(self):
        with patch.object(settings, "BCRYPT_ROUNDS", 11):
            hashed = hash_password("Correct-Horse-9")
        self.assertTrue(hashed.startswith("$2b$11$"), hashed[:7])
        self.assertTrue(verify_password("Correct-Horse-9", hashed))
        self.assertFalse(verify_password("wrong", hashed))

    def test_hashes_made_with_another_cost_still_verify(self):
        older = bcrypt.hashpw(b"Correct-Horse-9", bcrypt.gensalt(rounds=10)).decode()
        with patch.object(settings, "BCRYPT_ROUNDS", 12):
            self.assertTrue(verify_password("Correct-Horse-9", older))


class BcryptRoundsSetting(unittest.TestCase):
    def test_unset_means_the_cost_used_before_it_was_configurable(self):
        self.assertEqual(Settings.model_fields["BCRYPT_ROUNDS"].default, 10)

    def test_values_outside_10_to_14_are_refused_at_startup(self):
        for rounds in (4, 9, 15, 31):
            with self.subTest(rounds=rounds), self.assertRaises(ValidationError):
                Settings(BCRYPT_ROUNDS=rounds)

    def test_values_inside_the_range_are_accepted(self):
        for rounds in (10, 12, 14):
            with self.subTest(rounds=rounds):
                self.assertEqual(Settings(BCRYPT_ROUNDS=rounds).BCRYPT_ROUNDS, rounds)


if __name__ == "__main__":
    unittest.main()
