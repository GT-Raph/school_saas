from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from apps.core.models import SchoolOwnedModel


class TermResult(SchoolOwnedModel):
    """
    Final aggregate result for one student in one term.

    This does not replace SubjectResult.

    SubjectResult:
        Mathematics = 80
        English = 74

    TermResult:
        Overall Average = 77
        Failed Subjects = 0
        Attendance = 94%
    """

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        APPROVED = "approved", "Approved"
        PUBLISHED = "published", "Published"

    enrollment = models.ForeignKey(
        "academics.Enrollment",
        on_delete=models.PROTECT,
        related_name="term_results",
    )

    term = models.ForeignKey(
        "academics.Term",
        on_delete=models.PROTECT,
        related_name="student_term_results",
    )

    average_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
    )

    total_subjects = models.PositiveSmallIntegerField(
        default=0,
    )

    failed_subjects = models.PositiveSmallIntegerField(
        default=0,
    )

    attendance_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
    )

    class_teacher_comment = models.TextField(
        blank=True,
    )

    headteacher_comment = models.TextField(
        blank=True,
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
    )

    calculated_at = models.DateTimeField(
        auto_now=True,
    )

    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="term_results_approved",
    )

    approved_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    published_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="term_results_published",
    )

    published_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    class Meta:
        ordering = [
            "-term__academic_year__starts_on",
            "enrollment__student__last_name",
        ]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "enrollment",
                    "term",
                ],
                name=(
                    "one_term_result_per_"
                    "student_term"
                ),
            ),

            models.CheckConstraint(
                condition=(
                    models.Q(
                        average_score__gte=0
                    )
                    & models.Q(
                        average_score__lte=100
                    )
                ),
                name=(
                    "term_result_average_"
                    "between_0_100"
                ),
            ),
        ]

    def clean(self):
        errors = {}

        if (
            self.enrollment_id
            and self.school_id
            and self.enrollment.school_id
            != self.school_id
        ):
            errors["enrollment"] = (
                "Enrollment belongs to another school."
            )

        if (
            self.term_id
            and self.school_id
            and self.term.school_id
            != self.school_id
        ):
            errors["term"] = (
                "Term belongs to another school."
            )

        if (
            self.enrollment_id
            and self.term_id
            and self.enrollment.academic_year_id
            != self.term.academic_year_id
        ):
            errors["term"] = (
                "Term does not belong to the "
                "student's enrollment academic year."
            )

        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return (
            f"{self.enrollment.student} - "
            f"{self.term} - "
            f"{self.average_score}%"
        )


class ReportCard(SchoolOwnedModel):
    """
    Stores a historical snapshot of a published report.

    This protects old reports if grading/configuration changes later.
    """

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PUBLISHED = "published", "Published"

    term_result = models.OneToOneField(
        TermResult,
        on_delete=models.PROTECT,
        related_name="report_card",
    )

    report_number = models.CharField(
        max_length=100,
    )

    snapshot = models.JSONField(
        default=dict,
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
    )

    generated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="report_cards_generated",
    )

    generated_at = models.DateTimeField(
        auto_now_add=True,
    )

    published_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="report_cards_published",
    )

    published_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "school",
                    "report_number",
                ],
                name=(
                    "unique_report_number_"
                    "per_school"
                ),
            ),
        ]

    def clean(self):
        if (
            self.term_result_id
            and self.school_id
            and self.term_result.school_id
            != self.school_id
        ):
            raise ValidationError(
                {
                    "term_result": (
                        "Term result belongs "
                        "to another school."
                    )
                }
            )

    def __str__(self):
        return self.report_number
