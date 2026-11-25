from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Project user. Emails are stored lower-cased and are unique."""

    email = models.EmailField("email address", unique=True)
    affiliation = models.CharField(max_length=200, blank=True)
    bio = models.TextField(max_length=2000, blank=True)
    research_interests = models.JSONField(default=list, blank=True)

    class Meta:
        ordering = ["id"]

    def save(self, *args, **kwargs):
        if self.email:
            self.email = self.email.strip().lower()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.username
