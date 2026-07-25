from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from apps.core.models import SchoolOwnedModel


class Guardian(SchoolOwnedModel):
    """
    Parent or guardian record.

    One guardian can be linked to multiple students.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="guardian_profiles",
    )

    first_name = models.CharField(
        max_length=100,
    )

    last_name = models.CharField(
        max_length=100,
    )

    phone_number = models.CharField(
        max_length=30,
        blank=True,
    )

    alternative_phone = models.CharField(
        max_length=30,
        blank=True,
    )

    email = models.EmailField(
        blank=True,
    )

    occupation = models.CharField(
        max_length=150,
        blank=True,
    )

    address = models.TextField(
        blank=True,
    )

    is_active = models.BooleanField(
        default=True,
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
                    "user",
                ],
                name=(
                    "unique_guardian_user_"
                    "per_school"
                ),
            ),
        ]

        indexes = [
            models.Index(
                fields=[
                    "school",
                    "phone_number",
                ]
            ),
            models.Index(
                fields=[
                    "school",
                    "last_name",
                    "first_name",
                ]
            ),
        ]

    @property
    def full_name(self) -> str:
        return (
            f"{self.first_name} "
            f"{self.last_name}"
        ).strip()

    def __str__(self) -> str:
        return self.full_name


class StudentGuardian(SchoolOwnedModel):

    class Relationship(models.TextChoices):
        MOTHER = "mother", "Mother"
        FATHER = "father", "Father"
        STEPMOTHER = "stepmother", "Stepmother"
        STEPFATHER = "stepfather", "Stepfather"
        GRANDMOTHER = "grandmother", "Grandmother"
        GRANDFATHER = "grandfather", "Grandfather"
        AUNT = "aunt", "Aunt"
        UNCLE = "uncle", "Uncle"
        SIBLING = "sibling", "Sibling"
        GUARDIAN = "guardian", "Guardian"
        OTHER = "other", "Other"

    student = models.ForeignKey(
        "students.Student",
        on_delete=models.CASCADE,
        related_name="guardian_links",
    )

    guardian = models.ForeignKey(
        Guardian,
        on_delete=models.CASCADE,
        related_name="student_links",
    )

    relationship = models.CharField(
        max_length=30,
        choices=Relationship.choices,
        default=Relationship.GUARDIAN,
    )

    is_primary_contact = models.BooleanField(
        default=False,
    )

    financially_responsible = models.BooleanField(
        default=False,
    )

    receives_reports = models.BooleanField(
        default=True,
    )

    emergency_contact = models.BooleanField(
        default=False,
    )

    can_collect_student = models.BooleanField(
        default=False,
    )

    notes = models.TextField(
        blank=True,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "student",
                    "guardian",
                ],
                name=(
                    "unique_student_guardian_"
                    "relationship"
                ),
            ),
            models.UniqueConstraint(
                fields=[
                    "student",
                ],
                condition=models.Q(
                    is_primary_contact=True
                ),
                name=(
                    "one_primary_guardian_"
                    "per_student"
                ),
            ),
        ]

    def clean(self):
        errors = {}

        if (
            self.student_id
            and self.school_id
            and self.student.school_id
            != self.school_id
        ):
            errors["student"] = (
                "The student belongs to a "
                "different school."
            )

        if (
            self.guardian_id
            and self.school_id
            and self.guardian.school_id
            != self.school_id
        ):
            errors["guardian"] = (
                "The guardian belongs to a "
                "different school."
            )

        if errors:
            raise ValidationError(
                errors
            )

    def __str__(self) -> str:
        return (
            f"{self.guardian} -> "
            f"{self.student}"
        )