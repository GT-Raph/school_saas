from django.core.exceptions import (
    ValidationError,
)
from django.db import models

from apps.core.models import SchoolOwnedModel


class AcademicYear(SchoolOwnedModel):

    class Status(models.TextChoices):
        PLANNED = "planned", "Planned"
        ACTIVE = "active", "Active"
        CLOSED = "closed", "Closed"
        ARCHIVED = "archived", "Archived"

    name = models.CharField(
        max_length=50,
        help_text="Example: 2026/2027",
    )

    starts_on = models.DateField()

    ends_on = models.DateField()

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PLANNED,
    )

    is_current = models.BooleanField(
        default=False,
    )

    class Meta:
        ordering = [
            "-starts_on",
        ]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "school",
                    "name",
                ],
                name=(
                    "unique_academic_year_"
                    "name_per_school"
                ),
            ),

            models.UniqueConstraint(
                fields=[
                    "school",
                ],
                condition=models.Q(
                    is_current=True
                ),
                name=(
                    "one_current_academic_"
                    "year_per_school"
                ),
            ),

            models.CheckConstraint(
                condition=models.Q(
                    starts_on__lt=models.F(
                        "ends_on"
                    )
                ),
                name=(
                    "academic_year_start_"
                    "before_end"
                ),
            ),
        ]

    def __str__(self) -> str:
        return (
            f"{self.school.name} - "
            f"{self.name}"
        )


class Term(SchoolOwnedModel):

    name = models.CharField(
        max_length=50,
    )

    academic_year = models.ForeignKey(
        AcademicYear,
        on_delete=models.CASCADE,
        related_name="terms",
    )

    sequence = models.PositiveSmallIntegerField(
        help_text=(
            "1 for Term 1, "
            "2 for Term 2, etc."
        ),
    )

    starts_on = models.DateField()

    ends_on = models.DateField()

    is_current = models.BooleanField(
        default=False,
    )

    class Meta:
        ordering = [
            "academic_year",
            "sequence",
        ]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "school",
                    "academic_year",
                    "sequence",
                ],
                name=(
                    "unique_term_sequence_"
                    "per_academic_year"
                ),
            ),

            models.UniqueConstraint(
                fields=[
                    "school",
                    "academic_year",
                    "name",
                ],
                name=(
                    "unique_term_name_per_"
                    "academic_year"
                ),
            ),

            models.UniqueConstraint(
                fields=[
                    "school",
                    "academic_year",
                ],
                condition=models.Q(
                    is_current=True
                ),
                name=(
                    "one_current_term_per_"
                    "academic_year"
                ),
            ),

            models.CheckConstraint(
                condition=models.Q(
                    starts_on__lt=models.F(
                        "ends_on"
                    )
                ),
                name=(
                    "term_start_before_end"
                ),
            ),
        ]

    def clean(self):
        errors = {}

        if (
            self.academic_year_id
            and self.school_id
            and self.academic_year.school_id
            != self.school_id
        ):
            errors["academic_year"] = (
                "Academic year belongs "
                "to another school."
            )

        if self.academic_year_id:
            if (
                self.starts_on
                < self.academic_year.starts_on
            ):
                errors["starts_on"] = (
                    "Term cannot start before "
                    "the academic year."
                )

            if (
                self.ends_on
                > self.academic_year.ends_on
            ):
                errors["ends_on"] = (
                    "Term cannot end after "
                    "the academic year."
                )

        if errors:
            raise ValidationError(
                errors
            )

    def __str__(self) -> str:
        return (
            f"{self.academic_year.name} "
            f"- {self.name}"
        )


class ClassLevel(SchoolOwnedModel):
    """
    Academic progression level.

    Examples:
    Nursery 1
    KG 2
    Basic 1
    Basic 2
    JHS 1
    """

    name = models.CharField(
        max_length=100,
    )

    code = models.SlugField(
        max_length=50,
    )

    order = models.PositiveSmallIntegerField(
        help_text=(
            "Controls academic progression "
            "order."
        ),
    )

    next_level = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="previous_levels",
    )

    is_graduating_level = (
        models.BooleanField(
            default=False,
        )
    )

    is_active = models.BooleanField(
        default=True,
    )

    class Meta:
        ordering = [
            "order",
        ]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "school",
                    "code",
                ],
                name=(
                    "unique_class_level_"
                    "code_per_school"
                ),
            ),

            models.UniqueConstraint(
                fields=[
                    "school",
                    "order",
                ],
                name=(
                    "unique_class_level_"
                    "order_per_school"
                ),
            ),
        ]

    def clean(self):
        errors = {}

        if (
            self.next_level_id
            and self.next_level_id
            == self.id
        ):
            errors["next_level"] = (
                "A class level cannot point "
                "to itself."
            )

        if (
            self.next_level_id
            and self.school_id
            and self.next_level.school_id
            != self.school_id
        ):
            errors["next_level"] = (
                "Next class level must belong "
                "to the same school."
            )

        if errors:
            raise ValidationError(
                errors
            )

    def __str__(self) -> str:
        return self.name


class ClassSection(SchoolOwnedModel):
    """
    Actual section inside a level.

    Examples:
    Basic 4A
    Basic 4B
    JHS 1 Gold
    """

    level = models.ForeignKey(
        ClassLevel,
        on_delete=models.PROTECT,
        related_name="sections",
    )

    name = models.CharField(
        max_length=100,
        help_text="Example: A, B, Gold",
    )

    code = models.SlugField(
        max_length=50,
    )

    capacity = models.PositiveIntegerField(
        null=True,
        blank=True,
    )

    is_active = models.BooleanField(
        default=True,
    )

    class Meta:
        ordering = [
            "level__order",
            "name",
        ]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "school",
                    "level",
                    "code",
                ],
                name=(
                    "unique_class_section_"
                    "per_level"
                ),
            ),
        ]

    def clean(self):
        if (
            self.level_id
            and self.school_id
            and self.level.school_id
            != self.school_id
        ):
            raise ValidationError(
                {
                    "level": (
                        "Class level belongs "
                        "to another school."
                    )
                }
            )

    def __str__(self) -> str:
        return (
            f"{self.level.name} "
            f"{self.name}"
        )


class Subject(SchoolOwnedModel):

    name = models.CharField(
        max_length=150,
    )

    code = models.SlugField(
        max_length=50,
    )

    is_core = models.BooleanField(
        default=False,
    )

    is_active = models.BooleanField(
        default=True,
    )

    class Meta:
        ordering = [
            "name",
        ]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "school",
                    "code",
                ],
                name=(
                    "unique_subject_code_"
                    "per_school"
                ),
            ),
        ]

    def __str__(self) -> str:
        return self.name

class SubjectOffering(SchoolOwnedModel):
    """
    Represents a subject being taught to a particular class
    during a particular academic year.

    Example:
        Mathematics
        Basic 4A
        2026/2027
    """

    academic_year = models.ForeignKey(
        AcademicYear,
        on_delete=models.PROTECT,
        related_name="subject_offerings",
    )

    class_section = models.ForeignKey(
        ClassSection,
        on_delete=models.PROTECT,
        related_name="subject_offerings",
    )

    subject = models.ForeignKey(
        Subject,
        on_delete=models.PROTECT,
        related_name="offerings",
    )

    is_active = models.BooleanField(
        default=True,
    )

    class Meta:
        ordering = [
            "class_section",
            "subject__name",
        ]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "school",
                    "academic_year",
                    "class_section",
                    "subject",
                ],
                name=(
                    "unique_subject_offering_"
                    "per_class_year"
                ),
            ),
        ]

        indexes = [
            models.Index(
                fields=[
                    "school",
                    "academic_year",
                    "class_section",
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
            self.class_section_id
            and self.school_id
            and self.class_section.school_id != self.school_id
        ):
            errors["class_section"] = (
                "Class section belongs to another school."
            )

        if (
            self.subject_id
            and self.school_id
            and self.subject.school_id != self.school_id
        ):
            errors["subject"] = (
                "Subject belongs to another school."
            )

        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return (
            f"{self.subject.name} - "
            f"{self.class_section} - "
            f"{self.academic_year.name}"
        )


class TeacherAssignment(SchoolOwnedModel):
    """
    Assigns a teacher to a subject offering.

    Teacher changes can be preserved historically.
    """

    offering = models.ForeignKey(
        SubjectOffering,
        on_delete=models.CASCADE,
        related_name="teacher_assignments",
    )

    teacher = models.ForeignKey(
        "staff.Staff",
        on_delete=models.PROTECT,
        related_name="teaching_assignments",
    )

    starts_on = models.DateField()

    ends_on = models.DateField(
        null=True,
        blank=True,
    )

    is_primary = models.BooleanField(
        default=True,
    )

    is_active = models.BooleanField(
        default=True,
    )

    class Meta:
        ordering = [
            "-starts_on",
        ]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "offering",
                    "teacher",
                    "starts_on",
                ],
                name=(
                    "unique_teacher_assignment_"
                    "start"
                ),
            ),

            models.UniqueConstraint(
                fields=["offering"],
                condition=models.Q(
                    is_primary=True,
                    is_active=True,
                ),
                name=(
                    "one_active_primary_teacher_"
                    "per_offering"
                ),
            ),
        ]

    def clean(self):
        errors = {}

        if (
            self.offering_id
            and self.school_id
            and self.offering.school_id != self.school_id
        ):
            errors["offering"] = (
                "Subject offering belongs to another school."
            )

        if (
            self.teacher_id
            and self.school_id
            and self.teacher.school_id != self.school_id
        ):
            errors["teacher"] = (
                "Teacher belongs to another school."
            )

        if self.teacher_id and not self.teacher.is_teacher:
            errors["teacher"] = (
                "This staff member is not marked as a teacher."
            )

        if (
            self.starts_on
            and self.ends_on
            and self.ends_on < self.starts_on
        ):
            errors["ends_on"] = (
                "Assignment end date cannot be before start date."
            )

        if self.offering_id:
            year = self.offering.academic_year

            if self.starts_on < year.starts_on:
                errors["starts_on"] = (
                    "Teacher assignment cannot start before "
                    "the academic year."
                )

            if (
                self.ends_on
                and self.ends_on > year.ends_on
            ):
                errors["ends_on"] = (
                    "Teacher assignment cannot end after "
                    "the academic year."
                )

        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return (
            f"{self.teacher} -> "
            f"{self.offering}"
        )

class Enrollment(SchoolOwnedModel):
    """
    Places a student into a class for a specific academic year.

    A student should normally have only one primary enrollment
    per academic year.
    """

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        COMPLETED = (
            "completed",
            "Completed",
        )
        TRANSFERRED = (
            "transferred",
            "Transferred",
        )
        WITHDRAWN = (
            "withdrawn",
            "Withdrawn",
        )
        SUSPENDED = (
            "suspended",
            "Suspended",
        )

    student = models.ForeignKey(
        "students.Student",
        on_delete=models.PROTECT,
        related_name="enrollments",
    )

    academic_year = models.ForeignKey(
        AcademicYear,
        on_delete=models.PROTECT,
        related_name="enrollments",
    )

    class_section = models.ForeignKey(
        ClassSection,
        on_delete=models.PROTECT,
        related_name="enrollments",
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
    )

    enrolled_on = models.DateField()

    roll_number = models.CharField(
        max_length=50,
        blank=True,
    )

    notes = models.TextField(
        blank=True,
    )

    class Meta:
        ordering = [
            "-academic_year__starts_on",
            "class_section",
        ]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "school",
                    "student",
                    "academic_year",
                ],
                name=(
                    "one_student_enrollment_"
                    "per_academic_year"
                ),
            ),
        ]

        indexes = [
            models.Index(
                fields=[
                    "school",
                    "academic_year",
                    "status",
                ]
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
                "Student belongs to "
                "another school."
            )

        if (
            self.academic_year_id
            and self.school_id
            and self.academic_year.school_id
            != self.school_id
        ):
            errors["academic_year"] = (
                "Academic year belongs "
                "to another school."
            )

        if (
            self.class_section_id
            and self.school_id
            and self.class_section.school_id
            != self.school_id
        ):
            errors["class_section"] = (
                "Class section belongs "
                "to another school."
            )

        if errors:
            raise ValidationError(
                errors
            )

    def __str__(self) -> str:
        return (
            f"{self.student} - "
            f"{self.class_section} - "
            f"{self.academic_year}"
        )