"""Consistent JSON error envelope for every API error response.

    {"error": {"status": 400, "code": "validation_error", "message": "...", "fields": {...}}}
"""

import logging

from django.conf import settings
from rest_framework import exceptions, status
from rest_framework.response import Response
from rest_framework.views import exception_handler

logger = logging.getLogger(__name__)


def _first_message(data):
    if isinstance(data, list) and data:
        return _first_message(data[0])
    if isinstance(data, dict) and data:
        return _first_message(next(iter(data.values())))
    return str(data)


def api_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is None:
        if settings.DEBUG:
            return None
        logger.exception("Unhandled API error in %s", context.get("view").__class__.__name__)
        return Response(
            {"error": {"status": 500, "code": "server_error", "message": "Internal server error."}},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    data = response.data
    error = {"status": response.status_code}

    if isinstance(exc, exceptions.ValidationError):
        fields = data if isinstance(data, dict) else {"non_field_errors": data}
        error.update(code="validation_error", message=_first_message(fields), fields=fields)
    else:
        detail = data.get("detail", data) if isinstance(data, dict) else data
        codes = exc.get_codes() if isinstance(exc, exceptions.APIException) else None
        code = (
            (data.get("code") if isinstance(data, dict) else None)
            or (codes if isinstance(codes, str) else None)
            or getattr(exc, "default_code", "error")
        )
        error.update(code=str(code), message=str(detail))

    response.data = {"error": error}
    return response
