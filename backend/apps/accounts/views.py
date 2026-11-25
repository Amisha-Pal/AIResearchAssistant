from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .serializers import (
    ChangePasswordSerializer,
    LoginSerializer,
    LogoutSerializer,
    RegisterSerializer,
    TokenPairSerializer,
    UserSerializer,
)
from .services.tokens import issue_tokens, revoke_all_refresh_tokens

User = get_user_model()


class AuthThrottleMixin:
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth"


@extend_schema(tags=["auth"], responses={201: TokenPairSerializer})
class RegisterView(AuthThrottleMixin, generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]
    authentication_classes = []

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        body = {**issue_tokens(user), "user": UserSerializer(user).data}
        return Response(body, status=status.HTTP_201_CREATED)


@extend_schema(tags=["auth"])
class LoginView(AuthThrottleMixin, TokenObtainPairView):
    serializer_class = LoginSerializer


@extend_schema(tags=["auth"])
class RefreshView(AuthThrottleMixin, TokenRefreshView):
    pass


@extend_schema(tags=["auth"], request=LogoutSerializer, responses={204: None})
class LogoutView(APIView):
    """Revoke the given refresh token. The short-lived access token expires on its own."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            token = RefreshToken(serializer.validated_data["refresh"])
        except TokenError as exc:
            return Response(
                {"error": {"status": 400, "code": "token_not_valid", "message": str(exc)}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if str(token.get("user_id")) != str(request.user.id):
            return Response(
                {"error": {"status": 400, "code": "token_not_valid", "message": "Token does not belong to this user."}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        token.blacklist()
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(tags=["account"])
class MeView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "patch", "put", "head", "options"]

    def get_object(self):
        return self.request.user


@extend_schema(tags=["account"], request=ChangePasswordSerializer, responses={200: TokenPairSerializer})
class ChangePasswordView(AuthThrottleMixin, APIView):
    """Change password, revoke all existing refresh tokens and return a fresh token pair."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = request.user
        user.set_password(serializer.validated_data["new_password"])
        user.save(update_fields=["password"])
        revoke_all_refresh_tokens(user)
        return Response({**issue_tokens(user), "user": UserSerializer(user).data})
