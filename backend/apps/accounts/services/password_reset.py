import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode

logger = logging.getLogger(__name__)
User = get_user_model()


def build_reset_link(user):
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    # Values go in the URL fragment, which browsers never send to servers or in Referer headers.
    return f"{settings.FRONTEND_URL.rstrip('/')}/reset-password#uid={uid}&token={token}"


def send_password_reset_email(email):
    """Email a reset link if an active account with a usable password has this email. Never raises."""
    user = User.objects.filter(email__iexact=email.strip(), is_active=True).first()
    if user is None or not user.has_usable_password():
        return False
    minutes = settings.PASSWORD_RESET_TIMEOUT // 60
    body = (
        f"Hi {user.get_username()},\n\n"
        "We received a request to reset the password for your AI Research Assistant account.\n"
        f"Open this link within {minutes} minutes to choose a new password:\n\n"
        f"{build_reset_link(user)}\n\n"
        "If you did not ask for this, you can ignore this email; your password will not change.\n"
    )
    try:
        send_mail("Reset your AI Research Assistant password", body, None, [user.email])
    except Exception:
        logger.exception("Failed to send password reset email for user id=%s", user.pk)
        return False
    return True


def get_user_for_reset(uid, token):
    """Return the user if ``uid``/``token`` form a valid, unexpired reset link, else ``None``."""
    try:
        pk = force_str(urlsafe_base64_decode(uid))
        user = User.objects.get(pk=pk, is_active=True)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        return None
    return user if default_token_generator.check_token(user, token) else None
