"""Dependency health checks used by the /health endpoint."""

import logging
import time

import redis
from django.conf import settings
from django.db import connection

from ai_engine.config import get_ai_config
from ai_engine.llm.ollama_client import OllamaClient, OllamaError

logger = logging.getLogger(__name__)


def _timed(check):
    start = time.perf_counter()
    result = check()
    result["latency_ms"] = round((time.perf_counter() - start) * 1000, 1)
    return result


def check_database():
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT version()")
            version = cursor.fetchone()[0]
        return {"ok": True, "vendor": connection.vendor, "version": version.split(",")[0]}
    except Exception as exc:  # noqa: BLE001 - report any driver error
        logger.warning("Database health check failed: %s", exc)
        return {"ok": False, "error": str(exc)}


def check_redis():
    try:
        client = redis.Redis.from_url(settings.REDIS_URL, socket_connect_timeout=2, socket_timeout=2)
        client.ping()
        return {"ok": True}
    except Exception as exc:  # noqa: BLE001
        logger.warning("Redis health check failed: %s", exc)
        return {"ok": False, "error": str(exc)}


def check_ollama():
    config = get_ai_config()
    client = OllamaClient(config.ollama_base_url, timeout=3)
    try:
        info = client.status()
    except OllamaError as exc:
        return {"ok": False, "error": str(exc), "model": config.llm_model}
    installed = info["models"]
    return {
        "ok": True,
        "version": info["version"],
        "model": config.llm_model,
        "model_available": config.llm_model in installed,
        "installed_models": installed,
    }


_PUBLIC_KEYS = {"ok", "latency_ms", "model_available"}


def run_health_checks(detailed=True):
    """Run all checks. With detailed=False, versions and error messages are omitted."""
    checks = {
        "database": _timed(check_database),
        "redis": _timed(check_redis),
        "ollama": _timed(check_ollama),
    }
    if not checks["database"]["ok"]:
        status = "error"
    elif all(c["ok"] for c in checks.values()):
        status = "ok"
    else:
        status = "degraded"
    if not detailed:
        checks = {name: {k: v for k, v in c.items() if k in _PUBLIC_KEYS} for name, c in checks.items()}
    return {"status": status, "checks": checks}
