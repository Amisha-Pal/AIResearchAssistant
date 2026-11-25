from django.core.cache import cache
from django.test import override_settings
from rest_framework.test import APITestCase

LOCMEM_CACHE = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}


@override_settings(CACHES=LOCMEM_CACHE)
class IsolatedAPITestCase(APITestCase):
    """API test case with an in-memory cache, so throttle counters never leak between tests or into Redis."""

    def setUp(self):
        super().setUp()
        cache.clear()
