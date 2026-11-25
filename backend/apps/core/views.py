from django.conf import settings
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .services.health import run_health_checks


class HealthView(APIView):
    """Reports database, Redis and Ollama availability. Returns 503 only if the database is down."""

    permission_classes = [AllowAny]
    authentication_classes = []

    @extend_schema(responses={200: dict, 503: dict})
    def get(self, request):
        report = run_health_checks(detailed=settings.DEBUG)
        code = status.HTTP_503_SERVICE_UNAVAILABLE if report["status"] == "error" else status.HTTP_200_OK
        return Response(report, status=code)
