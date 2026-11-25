import os
from unittest import mock

from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APIClient

from config.env import env_bool, env_int, env_list, env_str

from .services import health

OLLAMA_OK = {"ok": True, "version": "0.5.0", "model": "qwen2.5:3b", "model_available": True, "installed_models": ["qwen2.5:3b"]}
OLLAMA_DOWN = {"ok": False, "error": "connection refused", "model": "qwen2.5:3b"}


class HealthEndpointTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse("health")

    @override_settings(DEBUG=True)
    @mock.patch.object(health, "check_redis", return_value={"ok": True})
    @mock.patch.object(health, "check_ollama", return_value=OLLAMA_OK)
    def test_all_services_up(self, *_):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["status"], "ok")
        self.assertTrue(body["checks"]["database"]["ok"])
        self.assertEqual(body["checks"]["database"]["vendor"], "postgresql")

    @mock.patch.object(health, "check_redis", return_value={"ok": True})
    @mock.patch.object(health, "check_ollama", return_value=OLLAMA_DOWN)
    def test_ollama_down_is_degraded_not_failed(self, *_):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "degraded")

    @mock.patch.object(health, "check_database", return_value={"ok": False, "error": "db down"})
    @mock.patch.object(health, "check_redis", return_value={"ok": True})
    @mock.patch.object(health, "check_ollama", return_value=OLLAMA_OK)
    def test_database_down_returns_503(self, *_):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["status"], "error")

    @override_settings(DEBUG=False)
    @mock.patch.object(health, "check_redis", return_value={"ok": False, "error": "secret host detail"})
    @mock.patch.object(health, "check_ollama", return_value=OLLAMA_DOWN)
    def test_details_hidden_when_debug_off(self, *_):
        body = self.client.get(self.url, secure=True).json()
        self.assertNotIn("error", body["checks"]["redis"])
        self.assertNotIn("version", body["checks"]["database"])
        self.assertNotIn("installed_models", body["checks"]["ollama"])

    def test_redis_check_reports_failure(self):
        with mock.patch.object(health.redis.Redis, "from_url", side_effect=ConnectionError("nope")):
            self.assertEqual(health.check_redis(), {"ok": False, "error": "nope"})


class ApiDocsTests(TestCase):
    def test_openapi_schema_available(self):
        response = self.client.get(reverse("api-schema"))
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"/api/v1/health/", response.content)

    def test_api_requires_auth_by_default(self):
        from rest_framework.settings import api_settings

        self.assertEqual(
            [p.__name__ for p in api_settings.DEFAULT_PERMISSION_CLASSES], ["IsAuthenticated"]
        )


class CeleryConfigTests(SimpleTestCase):
    def test_ping_task_runs_eagerly(self):
        from apps.core.tasks import ping

        self.assertEqual(ping.apply().get(), "pong")

    def test_celery_reads_django_settings(self):
        from config.celery import app

        self.assertEqual(app.conf.worker_prefetch_multiplier, 1)
        self.assertEqual(app.conf.task_serializer, "json")


class EnvHelperTests(SimpleTestCase):
    def test_parsers(self):
        with mock.patch.dict(os.environ, {"B": "yes", "I": "42", "L": "a, b,,c", "S": ""}):
            self.assertTrue(env_bool("B"))
            self.assertEqual(env_int("I", 0), 42)
            self.assertEqual(env_list("L"), ["a", "b", "c"])
            self.assertEqual(env_str("S", "fallback"), "fallback")

    def test_required_and_invalid_values_raise(self):
        with mock.patch.dict(os.environ, {"B": "maybe", "I": "x"}, clear=False):
            os.environ.pop("MISSING_VAR", None)
            with self.assertRaises(ImproperlyConfigured):
                env_str("MISSING_VAR", required=True)
            with self.assertRaises(ImproperlyConfigured):
                env_bool("B")
            with self.assertRaises(ImproperlyConfigured):
                env_int("I", 0)
