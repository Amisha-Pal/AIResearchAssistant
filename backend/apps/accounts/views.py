from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema
from rest_framework import generics, serializers, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .serializers import (
    AccessTokenSerializer,
    ChangePasswordSerializer,
    DetailSerializer,
    LoginSerializer,
    LogoutSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    RefreshRequestSerializer,
    RegisterSerializer,
    SessionTokenRefreshSerializer,
    TokenPairSerializer,
    UserSerializer,
)
from .services.cookies import clear_refresh_cookie, get_refresh_from_request, set_refresh_cookie
from .services.password_reset import send_password_reset_email
from .services.tokens import issue_tokens, revoke_all_refresh_tokens

User = get_user_model()


class AuthThrottleMixin:
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth"


def _token_error(message, http_status=status.HTTP_400_BAD_REQUEST):
    return Response(
        {"error": {"status": http_status, "code": "token_not_valid", "message": message}},
        status=http_status,
    )


def _session_response(user, http_status=status.HTTP_200_OK):
    tokens = issue_tokens(user)
    response = Response({**tokens, "user": UserSerializer(user).data}, status=http_status)
    return set_refresh_cookie(response, tokens["refresh"])


@extend_schema(tags=["auth"], responses={201: TokenPairSerializer})
class RegisterView(AuthThrottleMixin, generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]
    authentication_classes = []

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return _session_response(serializer.save(), status.HTTP_201_CREATED)


@extend_schema(tags=["auth"], responses={200: TokenPairSerializer})
class LoginView(AuthThrottleMixin, TokenObtainPairView):
    serializer_class = LoginSerializer
    authentication_classes = []

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == status.HTTP_200_OK:
            set_refresh_cookie(response, response.data["refresh"])
        return response


@extend_schema(tags=["auth"], request=RefreshRequestSerializer, responses={200: AccessTokenSerializer})
class RefreshView(AuthThrottleMixin, TokenRefreshView):
    """Rotate the refresh token (from the body or the httpOnly cookie) and return a new access token."""

    authentication_classes = []
    serializer_class = SessionTokenRefreshSerializer

    def post(self, request, *args, **kwargs):
        refresh = get_refresh_from_request(request)
        if not refresh:
            raise serializers.ValidationError({"refresh": ["This field is required."]})
        serializer = self.get_serializer(data={"refresh": refresh})
        try:
            serializer.is_valid(raise_exception=True)
        except TokenError as exc:
            response = self.handle_exception(InvalidToken(exc.args[0]))
            return clear_refresh_cookie(response)
        response = Response(serializer.validated_data, status=status.HTTP_200_OK)
        if "refresh" in serializer.validated_data:
            set_refresh_cookie(response, serializer.validated_data["refresh"])
        return response


@extend_schema(tags=["auth"], request=LogoutSerializer, responses={204: None})
class LogoutView(APIView):
    """Revoke the refresh token (body or cookie) and clear the cookie. The access token expires on its own."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        raw = get_refresh_from_request(request)
        if not raw:
            raise serializers.ValidationError({"refresh": ["This field is required."]})
        try:
            token = RefreshToken(raw)
        except TokenError as exc:
            return clear_refresh_cookie(_token_error(str(exc)))
        if str(token.get("user_id")) != str(request.user.id):
            return _token_error("Token does not belong to this user.")
        token.blacklist()
        return clear_refresh_cookie(Response(status=status.HTTP_204_NO_CONTENT))


@extend_schema(tags=["account"])
class MeView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "patch", "put", "head", "options"]

    def get_object(self):
        return self.request.user


@extend_schema(tags=["account"], request=ChangePasswordSerializer, responses={200: TokenPairSerializer})
class ChangePasswordView(AuthThrottleMixin, APIView):
    """Change password, revoke every existing session and return a fresh token pair."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = request.user
        user.set_password(serializer.validated_data["new_password"])
        user.save(update_fields=["password"])
        revoke_all_refresh_tokens(user)
        return _session_response(user)


@extend_schema(tags=["auth"], request=PasswordResetRequestSerializer, responses={200: DetailSerializer})
class PasswordResetRequestView(AuthThrottleMixin, APIView):
    """Email a single-use reset link. The response is identical whether or not the email is registered."""

    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        send_password_reset_email(serializer.validated_data["email"])
        return Response({"detail": "If an account exists for that email, a password reset link has been sent."})


@extend_schema(tags=["auth"], request=PasswordResetConfirmSerializer, responses={200: DetailSerializer})
class PasswordResetConfirmView(AuthThrottleMixin, APIView):
    """Set a new password from a reset link. The link stops working once the password changes."""

    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        user.set_password(serializer.validated_data["new_password"])
        user.save(update_fields=["password"])
        revoke_all_refresh_tokens(user)
        response = Response({"detail": "Your password has been reset. You can now log in."})
        return clear_refresh_cookie(response)
