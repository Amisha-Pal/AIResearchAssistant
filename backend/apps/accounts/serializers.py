from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer, TokenRefreshSerializer

from .services.password_reset import get_user_for_reset
from .services.tokens import token_matches_password

User = get_user_model()

MAX_INTERESTS = 20
MAX_INTEREST_LENGTH = 60


def _validate_unique_email(email, exclude_pk=None):
    email = email.strip().lower()
    qs = User.objects.filter(email__iexact=email)
    if exclude_pk is not None:
        qs = qs.exclude(pk=exclude_pk)
    if qs.exists():
        raise serializers.ValidationError("A user with this email already exists.")
    return email


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "affiliation",
            "bio",
            "research_interests",
            "date_joined",
            "last_login",
        )
        read_only_fields = ("id", "username", "date_joined", "last_login")

    def validate_email(self, value):
        return _validate_unique_email(value, exclude_pk=self.instance.pk if self.instance else None)

    def update(self, instance, validated_data):
        # Save only the edited columns so a stale request.user cannot overwrite
        # a concurrent password change or deactivation.
        for field, value in validated_data.items():
            setattr(instance, field, value)
        if validated_data:
            instance.save(update_fields=list(validated_data))
        return instance

    def validate_research_interests(self, value):
        if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
            raise serializers.ValidationError("Must be a list of strings.")
        cleaned = []
        for item in value:
            item = item.strip()
            if not item:
                continue
            if len(item) > MAX_INTEREST_LENGTH:
                raise serializers.ValidationError(f"Each interest must be at most {MAX_INTEREST_LENGTH} characters.")
            if item.lower() not in (c.lower() for c in cleaned):
                cleaned.append(item)
        if len(cleaned) > MAX_INTERESTS:
            raise serializers.ValidationError(f"At most {MAX_INTERESTS} interests are allowed.")
        return cleaned


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, style={"input_type": "password"})
    password_confirm = serializers.CharField(write_only=True, style={"input_type": "password"})

    class Meta:
        model = User
        fields = ("username", "email", "password", "password_confirm", "first_name", "last_name")
        extra_kwargs = {"email": {"required": True}}

    def validate_email(self, value):
        return _validate_unique_email(value)

    def validate_username(self, value):
        value = User.normalize_username(value)
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("A user with that username already exists.")
        return value

    def validate(self, attrs):
        if attrs["password"] != attrs.pop("password_confirm"):
            raise serializers.ValidationError({"password_confirm": "Passwords do not match."})
        candidate = User(username=attrs.get("username"), email=attrs.get("email"),
                         first_name=attrs.get("first_name", ""), last_name=attrs.get("last_name", ""))
        validate_password(attrs["password"], user=candidate)
        return attrs

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class LoginSerializer(TokenObtainPairSerializer):
    """Accepts either a username or an email address in the ``username`` field."""

    default_error_messages = {"no_active_account": "Invalid username/email or password."}

    def validate(self, attrs):
        identifier = User.normalize_username(attrs.get(self.username_field, "").strip())
        if "@" in identifier and not User.objects.filter(username=identifier).exists():
            user = User.objects.filter(email__iexact=identifier).only("username").first()
            if user is not None:
                identifier = user.username
        attrs[self.username_field] = identifier
        data = super().validate(attrs)
        data["user"] = UserSerializer(self.user).data
        return data


class SessionTokenRefreshSerializer(TokenRefreshSerializer):
    """Rejects refresh tokens issued before the user's current password was set."""

    def validate(self, attrs):
        refresh = self.token_class(attrs["refresh"])
        user = User.objects.filter(pk=refresh.get("user_id")).first()
        if user is None or not token_matches_password(refresh, user):
            raise TokenError("Token has been revoked.")
        return super().validate(attrs)


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField(required=False, help_text="Optional when the refresh cookie is sent.")


class RefreshRequestSerializer(serializers.Serializer):
    refresh = serializers.CharField(required=False, help_text="Optional when the refresh cookie is sent.")


class AccessTokenSerializer(serializers.Serializer):
    access = serializers.CharField()
    refresh = serializers.CharField()


class DetailSerializer(serializers.Serializer):
    detail = serializers.CharField()


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True, style={"input_type": "password"})
    new_password_confirm = serializers.CharField(write_only=True, style={"input_type": "password"})

    def validate(self, attrs):
        user = get_user_for_reset(attrs["uid"], attrs["token"])
        if user is None:
            raise serializers.ValidationError({"token": "This reset link is invalid or has expired."})
        if attrs["new_password"] != attrs["new_password_confirm"]:
            raise serializers.ValidationError({"new_password_confirm": "Passwords do not match."})
        validate_password(attrs["new_password"], user=user)
        attrs["user"] = user
        return attrs


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True, style={"input_type": "password"})
    new_password = serializers.CharField(write_only=True, style={"input_type": "password"})
    new_password_confirm = serializers.CharField(write_only=True, style={"input_type": "password"})

    def validate_current_password(self, value):
        if not self.context["request"].user.check_password(value):
            raise serializers.ValidationError("Current password is incorrect.")
        return value

    def validate(self, attrs):
        if attrs["new_password"] != attrs["new_password_confirm"]:
            raise serializers.ValidationError({"new_password_confirm": "Passwords do not match."})
        if attrs["new_password"] == attrs["current_password"]:
            raise serializers.ValidationError({"new_password": "New password must differ from the current one."})
        validate_password(attrs["new_password"], user=self.context["request"].user)
        return attrs


class TokenPairSerializer(serializers.Serializer):
    """Response shape for register and password change."""

    access = serializers.CharField()
    refresh = serializers.CharField()
    user = UserSerializer()
