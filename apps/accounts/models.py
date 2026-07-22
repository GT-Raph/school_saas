import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Authentication identity.

    A User is NOT automatically a Student, Teacher, Parent, or Staff member.
    Those business profiles will be separate models later.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    phone_number = models.CharField(
        max_length=30,
        blank=True,
    )

    is_platform_admin = models.BooleanField(
        default=False,
        help_text="Allows access to platform-level SaaS administration.",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    def __str__(self) -> str:
        return self.get_full_name() or self.username
    