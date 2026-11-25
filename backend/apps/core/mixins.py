from rest_framework.permissions import IsAuthenticated

from .permissions import IsOwner


class OwnedResourceMixin:
    """
    Scopes a viewset to the requesting user's own objects.

    Querysets are filtered by ``owner`` (so other users' objects return 404, not 403)
    and new objects are created with ``owner=request.user``.
    """

    permission_classes = [IsAuthenticated, IsOwner]

    def get_queryset(self):
        return super().get_queryset().filter(owner=self.request.user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)
