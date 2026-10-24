"""A trainer without a photo gets the default picture for their gender (core/media.py), read the same
loose way the app reads a trainee's (src/utils/traineeAvatar.ts genderKey): "male" or just "m", any
letter case, spaces around it ignored. Anything else keeps the female default, as before."""

import unittest

from app.core.media import default_trainer_avatar, resolve_trainer_avatar

MALE = "trainer_photos/default_male.png"
FEMALE = "trainer_photos/default_female.png"


class DefaultTrainerAvatar(unittest.TestCase):
    def test_male_however_it_was_typed(self):
        for gender in ("male", "Male", "MALE", " male ", "m", "M", " m "):
            with self.subTest(gender=gender):
                self.assertEqual(default_trainer_avatar(gender), MALE)

    def test_everything_else_keeps_the_female_default(self):
        for gender in ("female", "Female", "F", "f", "", "   ", None, "Other", "mf", "ma"):
            with self.subTest(gender=gender):
                self.assertEqual(default_trainer_avatar(gender), FEMALE)

    def test_a_real_photo_still_wins(self):
        self.assertEqual(resolve_trainer_avatar("trainer_photos/AGT1.jpg", "M"), "trainer_photos/AGT1.jpg")
        self.assertEqual(resolve_trainer_avatar("defaultfile.png", "M"), MALE)
        self.assertEqual(resolve_trainer_avatar(None, " m "), MALE)


if __name__ == "__main__":
    unittest.main()
