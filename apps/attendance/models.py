from django.core.exceptions import ValidationError
from django.db import models

from apps.core.models import SchoolOwnedModel


class AttendanceSession(SchoolOwnedModel):

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        SUBMITTED = "submitted", "Submitted"
        LOCKED = "locked", "Locked"

    academic_year = models.ForeignKey(
        "academics.AcademicYear",
        on_delete=models.PROTECT,
        related_name="attendance_sessions",
    )

    term = models.ForeignKey(
        "academics.Term",
        on_delete=models.PROTECT,
        related_name="attendance_sessions",
    )

    class_section = models.ForeignKey(
        "academics.ClassSection",
        on_delete=models.PROTECT,
        related_name="attendance_sessions",
    )

    attendance_date = models.DateField()

    taken_by = models.ForeignKey(
        "staff.Staff",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="attendance_sessions_taken",
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
    )

    notes = models.TextField(
        blank=True,
    )

    class Meta:
        ordering = [
            "-attendance_date",
        ]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "school",
                    "class_section",
                    "attendance_date",
                ],
                name=(
                    "one_daily_attendance_session_"
                    "per_class"
                ),
            ),
        ]

        indexes = [
            models.Index(
                fields=[
                    "school",
                    "attendance_date",
                ]
            ),
        ]

    def clean(self):
        errors = {}

        if (
            self.academic_year_id
            and self.school_id
            and self.academic_year.school_id != self.school_id
        ):
            errors["academic_year"] = (
                "Academic year belongs to another school."
            )

        if (
            self.term_id
            and self.school_id
            and self.term.school_id != self.school_id
        ):
            errors["term"] = (
                "Term belongs to another school."
            )

        if (
            self.class_section_id
            and self.school_id
            and self.class_section.school_id != self.school_id
        ):
            errors["class_section"] = (
                "Class belongs to another school."
            )

        if (
            self.taken_by_id
            and self.school_id
            and self.taken_by.school_id != self.school_id
        ):
            errors["taken_by"] = (
                "Staff member belongs to another school."
            )

        if (
            self.term_id
            and self.academic_year_id
            and self.term.academic_year_id
            != self.academic_year_id
        ):
            errors["term"] = (
                "Term does not belong to the selected academic year."
            )

        if self.term_id and self.attendance_date:
            if not (
                self.term.starts_on
                <= self.attendance_date
                <= self.term.ends_on
            ):
                errors["attendance_date"] = (
                    "Attendance date must fall within the term."
                )

        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return (
            f"{self.class_section} - "
            f"{self.attendance_date}"
        )


class AttendanceRecord(SchoolOwnedModel):

    class Status(models.TextChoices):
        PRESENT = "present", "Present"
        ABSENT = "absent", "Absent"
        LATE = "late", "Late"
        EXCUSED = "excused", "Excused"
        SICK = "sick", "Sick"

    session = models.ForeignKey(
        AttendanceSession,
        on_delete=models.CASCADE,
        related_name="records",
    )

    enrollment = models.ForeignKey(
        "academics.Enrollment",
        on_delete=models.PROTECT,
        related_name="attendance_records",
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PRESENT,
    )

    remarks = models.CharField(
        max_length=255,
        blank=True,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "session",
                    "enrollment",
                ],
                name=(
                    "unique_attendance_record_"
                    "per_session_student"
                ),
            ),
        ]

    def clean(self):
        errors = {}

        if (
            self.session_id
            and self.school_id
            and self.session.school_id != self.school_id
        ):
            errors["session"] = (
                "Attendance session belongs to another school."
            )

        if (
            self.enrollment_id
            and self.school_id
            and self.enrollment.school_id != self.school_id
        ):
            errors["enrollment"] = (
                "Enrollment belongs to another school."
            )

        if self.session_id and self.enrollment_id:

            if (
                self.enrollment.academic_year_id
                != self.session.academic_year_id
            ):
                errors["enrollment"] = (
                    "Student is not enrolled in this academic year."
                )

            if (
                self.enrollment.class_section_id
                != self.session.class_section_id
            ):
                errors["enrollment"] = (
                    "Student is not enrolled in this class."
                )

        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return (
            f"{self.enrollment.student} - "
            f"{self.status}"
        )