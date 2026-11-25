from django.conf import settings


def _cookie():
    return settings.AUTH_REFRESH_COOKIE


def get_refresh_from_request(request):
    """Refresh token from the JSON body (API clients) or the httpOnly cookie (browser app)."""
    return request.data.get("refresh") or request.COOKIES.get(_cookie()["NAME"])


def set_refresh_cookie(response, refresh):
    cookie = _cookie()
    response.set_cookie(
        cookie["NAME"],
        refresh,
        max_age=int(settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"].total_seconds()),
        path=cookie["PATH"],
        secure=cookie["SECURE"],
        httponly=True,
        samesite=cookie["SAMESITE"],
    )
    return response


def clear_refresh_cookie(response):
    cookie = _cookie()
    response.delete_cookie(cookie["NAME"], path=cookie["PATH"], samesite=cookie["SAMESITE"])
    return response
