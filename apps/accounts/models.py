import uuid
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from apps.core.models import(
    TimeStampedModel,
)


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

    must_change_password = models.BooleanField(
        default=False,
        help_text=(
            "Forces the user to change a temporary "
            "password before continuing."
        ),
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    def __str__(self) -> str:
        return self.get_full_name() or self.username


class LoginHandoff(
    TimeStampedModel
):
    """
    Short-lived, one-use credential used to move an
    authenticated user from the central login domain
    into a specific school's isolated session.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name=(
            "login_handoffs"
        ),
    )

    school = models.ForeignKey(
        "schools.School",
        on_delete=models.CASCADE,
        related_name=(
            "login_handoffs"
        ),
    )

    token_hash = models.CharField(
        max_length=64,
        unique=True,
        db_index=True,
    )

    expires_at = (
        models.DateTimeField(
            db_index=True,
        )
    )

    consumed_at = (
        models.DateTimeField(
            null=True,
            blank=True,
        )
    )

    class Meta:
        ordering = [
            "-created_at",
        ]

    def __str__(self):
        return (
            f"{self.user} → "
            f"{self.school}"
        )
    