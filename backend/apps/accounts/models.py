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

    @staticmethod
    def normalize_email_address(email):
        return (email or "").strip().lower()

    def clean(self):
        super().clean()
        self.email = self.normalize_email_address(self.email)

    def save(self, *args, **kwargs):
        self.email = self.normalize_email_address(self.email)
        if self.research_interests is None:
            self.research_interests = []
        super().save(*args, **kwargs)

    def __str__(self):
        return self.username
