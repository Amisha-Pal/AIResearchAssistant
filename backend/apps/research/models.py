from django.conf import settings
from django.db import models

from apps.core.models import TimeStampedModel


class ResearchProject(TimeStampedModel):
    """A user's research workspace; papers, chats and experiments are grouped under it."""

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        COMPLETED = "completed", "Completed"
        ARCHIVED = "archived", "Archived"

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="research_projects")
    title = models.CharField(max_length=200)
    description = models.TextField(max_length=5000, blank=True)
    research_question = models.TextField(max_length=2000, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE, db_index=True)
    tags = models.JSONField(default=list, blank=True)

    class Meta:
        ordering = ["-updated_at"]
        constraints = [
            models.UniqueConstraint(fields=["owner", "title"], name="unique_project_title_per_owner"),
        ]
        indexes = [models.Index(fields=["owner", "status"])]

    def save(self, *args, **kwargs):
        if self.tags is None:
            self.tags = []
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title
