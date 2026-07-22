from django.conf import settings
from django.db import models

from apps.core.models import SchoolOwnedModel


class Staff(SchoolOwnedModel):

    class EmploymentStatus(
        models.TextChoices
    ):
        ACTIVE = "active", "Active"
        ON_LEAVE = "on_leave", "On Leave"
        SUSPENDED = (
            "suspended",
            "Suspended",
        )
        RESIGNED = "resigned", "Resigned"
        TERMINATED = (
            "terminated",
            "Terminated",
        )
        RETIRED = "retired", "Retired"
        ARCHIVED = "archived", "Archived"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="staff_profiles",
    )

    employee_number = models.CharField(
        max_length=50,
    )

    first_name = models.CharField(
        max_length=100,
    )

    middle_name = models.CharField(
        max_length=100,
        blank=True,
    )

    last_name = models.CharField(
        max_length=100,
    )

    job_title = models.CharField(
        max_length=150,
        blank=True,
    )

    department = models.CharField(
        max_length=150,
        blank=True,
    )

    is_teacher = models.BooleanField(
        default=False,
        help_text="Indicates whether this staff member can be assigned to teach.",
    )

    phone_number = models.CharField(
        max_length=30,
        blank=True,
    )

    email = models.EmailField(
        blank=True,
    )

    employment_date = models.DateField(
        null=True,
        blank=True,
    )

    employment_status = models.CharField(
        max_length=30,
        choices=EmploymentStatus.choices,
        default=EmploymentStatus.ACTIVE,
    )

    notes = models.TextField(
        blank=True,
    )

    class Meta:
        ordering = [
            "last_name",
            "first_name",
        ]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "school",
                    "employee_number",
                ],
                name=(
                    "unique_employee_number_"
                    "per_school"
                ),
            ),
            models.UniqueConstraint(
                fields=[
                    "school",
                    "user",
                ],
                name=(
                    "unique_staff_user_"
                    "per_school"
                ),
            ),
        ]

        indexes = [
            models.Index(
                fields=[
                    "school",
                    "employment_status",
                ]
            ),
        ]

    @property
    def full_name(self) -> str:
        names = [
            self.first_name,
            self.middle_name,
            self.last_name,
        ]

        return " ".join(
            name.strip()
            for name in names
            if name and name.strip()
        )

    def __str__(self) -> str:
        return (
            f"{self.full_name} "
            f"({self.employee_number})"
        )
    
    