from drf_spectacular.contrib.rest_framework_simplejwt import SimpleJWTScheme
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import AuthenticationFailed


class RevocableJWTAuthentication(JWTAuthentication):
    """Rejects access tokens issued before the user's last password change."""

    def get_user(self, validated_token):
        user = super().get_user(validated_token)
        cutoff = getattr(user, "tokens_valid_after", None)
        if cutoff is not None and validated_token.get("iat", 0) < int(cutoff.timestamp()):
            raise AuthenticationFailed("Token has been revoked.", code="token_not_valid")
        return user


class RevocableJWTScheme(SimpleJWTScheme):
    target_class = "apps.accounts.authentication.RevocableJWTAuthentication"
