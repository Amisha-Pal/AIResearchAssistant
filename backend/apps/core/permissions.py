from rest_framework.permissions import BasePermission


class IsOwner(BasePermission):
    """Object-level check that the object's ``owner`` is the requesting user."""

    message = "You do not have access to this resource."

    def has_object_permission(self, request, view, obj):
        return getattr(obj, "owner_id", None) == request.user.id
