from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import TestCase


class UserModelTests(TestCase):
    def test_custom_user_model_is_active(self):
        self.assertEqual(get_user_model()._meta.label, "accounts.User")

    def test_password_is_hashed(self):
        user = get_user_model().objects.create_user("ada", "ada@example.com", "s3cure-Passw0rd")
        self.assertNotEqual(user.password, "s3cure-Passw0rd")
        self.assertTrue(user.check_password("s3cure-Passw0rd"))

    def test_email_must_be_unique(self):
        User = get_user_model()
        User.objects.create_user("ada", "ada@example.com", "s3cure-Passw0rd")
        with self.assertRaises(IntegrityError):
            User.objects.create_user("grace", "ada@example.com", "s3cure-Passw0rd")
