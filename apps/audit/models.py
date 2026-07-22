from django.conf import settings
from django.db import models

from apps.core.models import TimeStampedModel
from apps.schools.models import School


class AuditEvent(TimeStampedModel):
    """
    Immutable-style record describing important actions.

    We should avoid editing or deleting audit events through normal
    application workflows.
    """

    school = models.ForeignKey(
        School,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_events",
    )

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_events",
    )

    action = models.CharField(
        max_length=120,
    )

    object_type = models.CharField(
        max_length=120,
        blank=True,
    )

    object_id = models.CharField(
        max_length=100,
        blank=True,
    )

    changes = models.JSONField(
        default=dict,
        blank=True,
    )

    metadata = models.JSONField(
        default=dict,
        blank=True,
    )

    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
    )

    class Meta:
        ordering = [
            "-created_at",
        ]

        indexes = [
            models.Index(
                fields=["school", "created_at"],
            ),
            models.Index(
                fields=["action"],
            ),
        ]

    def __str__(self) -> str:
        return f"{self.action} - {self.created_at}"