from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.utils import get_md5_hash_password


def issue_tokens(user):
    refresh = RefreshToken.for_user(user)
    return {"access": str(refresh.access_token), "refresh": str(refresh)}


def token_matches_password(token, user):
    """False when ``token`` was issued before the user's current password was set (``CHECK_REVOKE_TOKEN``)."""
    return token.get(api_settings.REVOKE_TOKEN_CLAIM) == get_md5_hash_password(user.password)


def revoke_all_refresh_tokens(user):
    """Blacklist every outstanding refresh token of ``user`` (e.g. after a password change)."""
    tokens = OutstandingToken.objects.filter(user=user).exclude(blacklistedtoken__isnull=False)
    BlacklistedToken.objects.bulk_create([BlacklistedToken(token=t) for t in tokens], ignore_conflicts=True)
