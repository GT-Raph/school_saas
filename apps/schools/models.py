from django.conf import settings
from django.contrib.auth.models import Permission
from django.db import models

from apps.core.models import TimeStampedModel


class School(TimeStampedModel):
    class Status(models.TextChoices):
        TRIAL = "trial", "Trial"
        ACTIVE = "active", "Active"
        SUSPENDED = "suspended", "Suspended"
        CLOSED = "closed", "Closed"

    name = models.CharField(
        max_length=255,
    )

    slug = models.SlugField(
        max_length=120,
        unique=True,
    )

    admission_prefix = models.CharField(
        max_length=10,
        blank=True,
        help_text=(
            "Prefix used for automatically generated "
            "student admission numbers."
        ),
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.TRIAL,
    )

    timezone = models.CharField(
        max_length=100,
        default="Africa/Accra",
    )

    currency = models.CharField(
        max_length=3,
        default="GHS",
    )

    default_language = models.CharField(
        max_length=10,
        default="en",
    )

    class Meta:
        permissions = [
            (
                "manage_school_settings",
                "Can manage school settings",
            ),
            (
                "manage_school_users",
                "Can manage school users",
            ),
            (
                "manage_school_roles",
                "Can manage school roles and permissions",
            ),
        ]

    def __str__(self) -> str:
        return self.name


class SchoolDomain(TimeStampedModel):
    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name="domains",
    )

    domain = models.CharField(
        max_length=255,
        unique=True,
    )

    is_primary = models.BooleanField(
        default=False,
    )

    is_verified = models.BooleanField(
        default=False,
    )

    def __str__(self) -> str:
        return self.domain


class SchoolRole(TimeStampedModel):
    """
    Tenant-specific role.

    Examples:
    - School Administrator
    - Academic Administrator
    - Accountant
    - Teacher
    - Admissions Officer
    """

    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name="roles",
    )

    name = models.CharField(
        max_length=100,
    )

    code = models.SlugField(
        max_length=100,
    )

    permissions = models.ManyToManyField(
        Permission,
        blank=True,
        related_name="school_roles",
    )

    is_system_role = models.BooleanField(
        default=False,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["school", "code"],
                name="unique_role_code_per_school",
            )
        ]

    def __str__(self) -> str:
        return f"{self.school.name} - {self.name}"


class SchoolMembership(TimeStampedModel):
    """
    Connects a login account to a tenant.

    A single User may belong to multiple schools.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="school_memberships",
    )

    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name="memberships",
    )

    roles = models.ManyToManyField(
        SchoolRole,
        blank=True,
        related_name="memberships",
    )

    is_active = models.BooleanField(
        default=True,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "school"],
                name="unique_user_membership_per_school",
            )
        ]

        indexes = [
            models.Index(
                fields=["school", "is_active"],
            )
        ]

    def __str__(self) -> str:
        return f"{self.user} @ {self.school}"
    
class SchoolBranding(TimeStampedModel):
    """
    Tenant-specific visual configuration.

    Schools can customize their appearance
    without touching source code.
    """

    school = models.OneToOneField(
        School,
        on_delete=models.CASCADE,
        related_name="branding",
    )

    logo_url = models.URLField(
        blank=True,
    )

    favicon_url = models.URLField(
        blank=True,
    )

    login_background_url = models.URLField(
        blank=True,
    )

    primary_color = models.CharField(
        max_length=20,
        default="#111827",
    )

    secondary_color = models.CharField(
        max_length=20,
        default="#FFFFFF",
    )

    accent_color = models.CharField(
        max_length=20,
        default="#2563EB",
    )

    motto = models.CharField(
        max_length=255,
        blank=True,
    )

    def __str__(self):
        return f"{self.school.name} Branding"