from django.conf import settings
from django.db import models

from apps.core.models import SchoolOwnedModel


class Student(SchoolOwnedModel):

    class Gender(models.TextChoices):
        MALE = "male", "Male"
        FEMALE = "female", "Female"
        OTHER = "other", "Other"
        UNSPECIFIED = "unspecified", "Unspecified"

    class Status(models.TextChoices):
        APPLICANT = "applicant", "Applicant"
        ADMITTED = "admitted", "Admitted"
        ACTIVE = "active", "Active"
        SUSPENDED = "suspended", "Suspended"
        TRANSFERRED = "transferred", "Transferred"
        WITHDRAWN = "withdrawn", "Withdrawn"
        GRADUATED = "graduated", "Graduated"
        ARCHIVED = "archived", "Archived"

    # A student does not necessarily need a login account.
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="student_profiles",
    )

    admission_number = models.CharField(
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

    date_of_birth = models.DateField(
        null=True,
        blank=True,
    )

    gender = models.CharField(
        max_length=20,
        choices=Gender.choices,
        default=Gender.UNSPECIFIED,
    )

    admission_date = models.DateField(
        null=True,
        blank=True,
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
    )

    phone_number = models.CharField(
        max_length=30,
        blank=True,
    )

    email = models.EmailField(
        blank=True,
    )

    photo_url = models.URLField(
        blank=True,
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
                    "admission_number",
                ],
                name=(
                    "unique_student_admission_"
                    "number_per_school"
                ),
            ),
            models.UniqueConstraint(
                fields=[
                    "school",
                    "user",
                ],
                name=(
                    "unique_student_user_"
                    "per_school"
                ),
            ),
        ]

        indexes = [
            models.Index(
                fields=[
                    "school",
                    "status",
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
            f"({self.admission_number})"
        )
    
class StudentImportBatch(SchoolOwnedModel):

    class Status(models.TextChoices):
        STAGED = "staged", "Staged"
        PROCESSING = "processing", "Processing"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"
        CANCELLED = "cancelled", "Cancelled"

    original_filename = models.CharField(
        max_length=255,
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.STAGED,
    )

    total_rows = models.PositiveIntegerField(
        default=0,
    )

    valid_rows = models.PositiveIntegerField(
        default=0,
    )

    invalid_rows = models.PositiveIntegerField(
        default=0,
    )

    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="student_import_batches",
    )

    completed_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    error_message = models.TextField(
        blank=True,
    )

    class Meta:
        ordering = [
            "-created_at",
        ]

    def __str__(self):
        return (
            f"{self.original_filename} "
            f"({self.get_status_display()})"
        )


class StudentImportRow(SchoolOwnedModel):

    batch = models.ForeignKey(
        StudentImportBatch,
        on_delete=models.CASCADE,
        related_name="rows",
    )

    row_number = models.PositiveIntegerField()

    raw_data = models.JSONField(
        default=dict,
    )

    normalized_data = models.JSONField(
        default=dict,
    )

    errors = models.JSONField(
        default=list,
    )

    is_valid = models.BooleanField(
        default=False,
    )

    imported_student = models.ForeignKey(
        Student,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="import_rows",
    )

    class Meta:
        ordering = [
            "row_number",
        ]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "batch",
                    "row_number",
                ],
                name=(
                    "unique_student_import_"
                    "row_number"
                ),
            ),
        ]

    def __str__(self):
        return (
            f"{self.batch.original_filename} "
            f"Row {self.row_number}"
        )