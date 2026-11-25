from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Project user. Defined before the first migration so it can be extended safely later."""

    email = models.EmailField("email address", unique=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return self.username
