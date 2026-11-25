from unittest import mock

from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import TestCase
from django.urls import reverse
from rest_framework.throttling import ScopedRateThrottle
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken

from apps.core.testing import IsolatedAPITestCase

User = get_user_model()
PASSWORD = "s3cure-Passw0rd!"


class UserModelTests(TestCase):
    def test_custom_user_model_is_active(self):
        self.assertEqual(User._meta.label, "accounts.User")

    def test_password_is_hashed(self):
        user = User.objects.create_user("ada", "ada@example.com", PASSWORD)
        self.assertNotEqual(user.password, PASSWORD)
        self.assertTrue(user.check_password(PASSWORD))

    def test_email_is_normalized_and_unique(self):
        user = User.objects.create_user("ada", "  Ada@Example.COM ", PASSWORD)
        self.assertEqual(user.email, "ada@example.com")
        with self.assertRaises(IntegrityError):
            User.objects.create_user("grace", "ADA@example.com", PASSWORD)


class RegisterTests(IsolatedAPITestCase):
    url = reverse("auth-register")

    def payload(self, **overrides):
        data = {
            "username": "ada",
            "email": "ada@example.com",
            "password": PASSWORD,
            "password_confirm": PASSWORD,
            "first_name": "Ada",
            "last_name": "Lovelace",
        }
        data.update(overrides)
        return data

    def test_register_returns_tokens_and_user(self):
        response = self.client.post(self.url, self.payload(), format="json")
        self.assertEqual(response.status_code, 201, response.content)
        body = response.json()
        self.assertIn("access", body)
        self.assertIn("refresh", body)
        self.assertEqual(body["user"]["username"], "ada")
        self.assertNotIn("password", body["user"])
        self.assertTrue(User.objects.get(username="ada").check_password(PASSWORD))

    def test_duplicate_email_case_insensitive(self):
        User.objects.create_user("existing", "ada@example.com", PASSWORD)
        response = self.client.post(self.url, self.payload(email="ADA@Example.com"), format="json")
        self.assertEqual(response.status_code, 400)
        error = response.json()["error"]
        self.assertEqual(error["code"], "validation_error")
        self.assertIn("email", error["fields"])

    def test_password_mismatch(self):
        response = self.client.post(self.url, self.payload(password_confirm="different-Passw0rd"), format="json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("password_confirm", response.json()["error"]["fields"])

    def test_weak_password_rejected(self):
        response = self.client.post(self.url, self.payload(password="12345678", password_confirm="12345678"), format="json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("non_field_errors", response.json()["error"]["fields"])

    def test_missing_fields(self):
        response = self.client.post(self.url, {}, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertTrue({"username", "email", "password"} <= set(response.json()["error"]["fields"]))


class LoginRefreshLogoutTests(IsolatedAPITestCase):
    def setUp(self):
        super().setUp()
        self.user = User.objects.create_user("ada", "ada@example.com", PASSWORD)

    def login(self, identifier, password=PASSWORD):
        return self.client.post(reverse("auth-login"), {"username": identifier, "password": password}, format="json")

    def test_login_with_username(self):
        response = self.login("ada")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["user"]["email"], "ada@example.com")

    def test_login_with_email_any_case(self):
        self.assertEqual(self.login("ADA@example.com").status_code, 200)

    def test_wrong_password(self):
        response = self.login("ada", "wrong-password")
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["error"]["code"], "no_active_account")

    def test_inactive_user_cannot_login(self):
        self.user.is_active = False
        self.user.save()
        self.assertEqual(self.login("ada").status_code, 401)

    def test_refresh_rotates_and_blacklists_old_token(self):
        refresh = self.login("ada").json()["refresh"]
        response = self.client.post(reverse("auth-refresh"), {"refresh": refresh}, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(response.json()["refresh"], refresh)
        reuse = self.client.post(reverse("auth-refresh"), {"refresh": refresh}, format="json")
        self.assertEqual(reuse.status_code, 401)

    def test_logout_blacklists_refresh_token(self):
        tokens = self.login("ada").json()
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")
        response = self.client.post(reverse("auth-logout"), {"refresh": tokens["refresh"]}, format="json")
        self.assertEqual(response.status_code, 204)
        reuse = self.client.post(reverse("auth-refresh"), {"refresh": tokens["refresh"]}, format="json")
        self.assertEqual(reuse.status_code, 401)

    def test_logout_rejects_other_users_token(self):
        User.objects.create_user("grace", "grace@example.com", PASSWORD)
        other_refresh = self.login("grace").json()["refresh"]
        access = self.login("ada").json()["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        response = self.client.post(reverse("auth-logout"), {"refresh": other_refresh}, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertFalse(BlacklistedToken.objects.exists())

    def test_logout_requires_auth(self):
        response = self.client.post(reverse("auth-logout"), {"refresh": "x"}, format="json")
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["error"]["code"], "not_authenticated")

    def test_logout_invalid_token(self):
        access = self.login("ada").json()["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        response = self.client.post(reverse("auth-logout"), {"refresh": "garbage"}, format="json")
        self.assertEqual(response.status_code, 400)

    @mock.patch.object(ScopedRateThrottle, "THROTTLE_RATES", {"auth": "3/min"})
    def test_auth_endpoints_are_throttled(self):
        codes = [self.login("ada", "wrong").status_code for _ in range(4)]
        self.assertEqual(codes[:3], [401, 401, 401])
        self.assertEqual(codes[3], 429)
        self.assertEqual(self.login("ada", "wrong").json()["error"]["code"], "throttled")


class ProfileTests(IsolatedAPITestCase):
    def setUp(self):
        super().setUp()
        self.user = User.objects.create_user("ada", "ada@example.com", PASSWORD)
        self.client.force_authenticate(self.user)
        self.url = reverse("auth-me")

    def test_get_profile(self):
        body = self.client.get(self.url).json()
        self.assertEqual(body["username"], "ada")
        self.assertEqual(body["research_interests"], [])

    def test_update_profile(self):
        response = self.client.patch(
            self.url,
            {"affiliation": "Analytical Engine Lab", "research_interests": [" NLP ", "nlp", "RAG"], "username": "hacker"},
            format="json",
        )
        self.assertEqual(response.status_code, 200, response.content)
        self.user.refresh_from_db()
        self.assertEqual(self.user.affiliation, "Analytical Engine Lab")
        self.assertEqual(self.user.research_interests, ["NLP", "RAG"])
        self.assertEqual(self.user.username, "ada")

    def test_cannot_take_another_users_email(self):
        User.objects.create_user("grace", "grace@example.com", PASSWORD)
        response = self.client.patch(self.url, {"email": "Grace@example.com"}, format="json")
        self.assertEqual(response.status_code, 400)

    def test_invalid_interests(self):
        response = self.client.patch(self.url, {"research_interests": "nlp"}, format="json")
        self.assertEqual(response.status_code, 400)

    def test_requires_auth(self):
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get(self.url).status_code, 401)


class ChangePasswordTests(IsolatedAPITestCase):
    def setUp(self):
        super().setUp()
        self.user = User.objects.create_user("ada", "ada@example.com", PASSWORD)
        self.tokens = self.client.post(
            reverse("auth-login"), {"username": "ada", "password": PASSWORD}, format="json"
        ).json()
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.tokens['access']}")
        self.url = reverse("auth-password-change")

    def change(self, current=PASSWORD, new="An0ther-strong-pass", confirm=None):
        return self.client.post(
            self.url,
            {"current_password": current, "new_password": new, "new_password_confirm": confirm or new},
            format="json",
        )

    def test_change_password_revokes_old_refresh_tokens(self):
        response = self.change()
        self.assertEqual(response.status_code, 200, response.content)
        self.assertIn("refresh", response.json())
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("An0ther-strong-pass"))
        old = self.client.post(reverse("auth-refresh"), {"refresh": self.tokens["refresh"]}, format="json")
        self.assertEqual(old.status_code, 401)
        new = self.client.post(reverse("auth-refresh"), {"refresh": response.json()["refresh"]}, format="json")
        self.assertEqual(new.status_code, 200)

    def test_wrong_current_password(self):
        response = self.change(current="nope")
        self.assertEqual(response.status_code, 400)
        self.assertIn("current_password", response.json()["error"]["fields"])

    def test_mismatch_and_weak(self):
        self.assertEqual(self.change(confirm="different-Passw0rd").status_code, 400)
        self.assertEqual(self.change(new="password").status_code, 400)

    def test_same_password_rejected(self):
        self.assertEqual(self.change(new=PASSWORD).status_code, 400)
