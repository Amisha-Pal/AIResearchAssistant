from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import viewsets

from apps.core.mixins import OwnedResourceMixin

from .models import ResearchProject
from .serializers import ResearchProjectSerializer


@extend_schema_view(
    list=extend_schema(
        tags=["projects"],
        parameters=[OpenApiParameter("status", str, enum=ResearchProject.Status.values, description="Filter by status")],
    ),
    retrieve=extend_schema(tags=["projects"]),
    create=extend_schema(tags=["projects"]),
    update=extend_schema(tags=["projects"]),
    partial_update=extend_schema(tags=["projects"]),
    destroy=extend_schema(tags=["projects"]),
)
class ResearchProjectViewSet(OwnedResourceMixin, viewsets.ModelViewSet):
    """CRUD for the current user's research projects. Supports ?search=, ?status= and ?ordering=."""

    queryset = ResearchProject.objects.all()
    serializer_class = ResearchProjectSerializer
    search_fields = ("title", "description", "research_question")
    ordering_fields = ("title", "created_at", "updated_at", "status")

    def get_queryset(self):
        queryset = super().get_queryset()
        status = self.request.query_params.get("status")
        if status in ResearchProject.Status.values:
            queryset = queryset.filter(status=status)
        return queryset
