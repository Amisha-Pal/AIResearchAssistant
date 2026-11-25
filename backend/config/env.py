"""Small helpers for reading typed values from environment variables."""

import os

from django.core.exceptions import ImproperlyConfigured

_TRUE = {"1", "true", "yes", "on"}
_FALSE = {"0", "false", "no", "off", ""}


def env_str(name, default=None, required=False):
    value = os.environ.get(name)
    if value is None or value == "":
        if required:
            raise ImproperlyConfigured(f"Environment variable {name} is required.")
        return default
    return value


def env_bool(name, default=False):
    value = os.environ.get(name)
    if value is None:
        return default
    normalized = value.strip().lower()
    if normalized in _TRUE:
        return True
    if normalized in _FALSE:
        return False
    raise ImproperlyConfigured(f"Environment variable {name} must be a boolean, got {value!r}.")


def env_int(name, default):
    value = os.environ.get(name)
    if value is None or value.strip() == "":
        return default
    try:
        return int(value)
    except ValueError as exc:
        raise ImproperlyConfigured(f"Environment variable {name} must be an integer, got {value!r}.") from exc


def env_float(name, default):
    value = os.environ.get(name)
    if value is None or value.strip() == "":
        return default
    try:
        return float(value)
    except ValueError as exc:
        raise ImproperlyConfigured(f"Environment variable {name} must be a number, got {value!r}.") from exc


def env_list(name, default=None):
    value = os.environ.get(name)
    if value is None:
        return list(default or [])
    return [item.strip() for item in value.split(",") if item.strip()]
