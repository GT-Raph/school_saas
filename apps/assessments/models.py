from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from apps.core.models import SchoolOwnedModel


class AssessmentScheme(SchoolOwnedModel):
    """
    Example:

    Standard Basic School Scheme

    Classwork: 30%
    Quiz:      10%
    Exam:      60%
    """

    name = models.CharField(
        max_length=150,
    )

    code = models.SlugField(
        max_length=100,
    )

    academic_year = models.ForeignKey(
        "academics.AcademicYear",
        on_delete=models.PROTECT,
        related_name="assessment_schemes",
    )

    is_active = models.BooleanField(
        default=True,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "school",
                    "academic_year",
                    "code",
                ],
                name=(
                    "unique_assessment_scheme_"
                    "per_year"
                ),
            ),
        ]

    def clean(self):
        if (
            self.academic_year_id
            and self.school_id
            and self.academic_year.school_id != self.school_id
        ):
            raise ValidationError(
                {
                    "academic_year":
                    "Academic year belongs to another school."
                }
            )

    def __str__(self):
        return self.name


class AssessmentCategory(SchoolOwnedModel):

    scheme = models.ForeignKey(
        AssessmentScheme,
        on_delete=models.CASCADE,
        related_name="categories",
    )

    name = models.CharField(
        max_length=100,
    )

    code = models.SlugField(
        max_length=50,
    )

    weight = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="Percentage contribution. Example: 30.00",
    )

    sequence = models.PositiveSmallIntegerField(
        default=1,
    )

    class Meta:
        ordering = [
            "sequence",
        ]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "scheme",
                    "code",
                ],
                name=(
                    "unique_assessment_category_"
                    "per_scheme"
                ),
            ),

            models.CheckConstraint(
                condition=models.Q(
                    weight__gt=0
                )
                & models.Q(
                    weight__lte=100
                ),
                name=(
                    "assessment_category_weight_"
                    "valid"
                ),
            ),
        ]

    def clean(self):
        if (
            self.scheme_id
            and self.school_id
            and self.scheme.school_id != self.school_id
        ):
            raise ValidationError(
                {
                    "scheme":
                    "Assessment scheme belongs to another school."
                }
            )

    def __str__(self):
        return (
            f"{self.name} ({self.weight}%)"
        )


class GradeScale(SchoolOwnedModel):

    name = models.CharField(
        max_length=150,
    )

    code = models.SlugField(
        max_length=100,
    )

    is_active = models.BooleanField(
        default=True,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "school",
                    "code",
                ],
                name=(
                    "unique_grade_scale_"
                    "per_school"
                ),
            ),
        ]

    def __str__(self):
        return self.name


class GradeBand(SchoolOwnedModel):

    grade_scale = models.ForeignKey(
        GradeScale,
        on_delete=models.CASCADE,
        related_name="bands",
    )

    grade = models.CharField(
        max_length=20,
    )

    label = models.CharField(
        max_length=100,
        blank=True,
    )

    minimum_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
    )

    maximum_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
    )

    remark = models.CharField(
        max_length=150,
        blank=True,
    )

    class Meta:
        ordering = [
            "-minimum_score",
        ]

        constraints = [
            models.CheckConstraint(
                condition=models.Q(
                    minimum_score__gte=0
                ),
                name="grade_minimum_not_negative",
            ),

            models.CheckConstraint(
                condition=models.Q(
                    maximum_score__lte=100
                ),
                name="grade_maximum_not_over_100",
            ),

            models.CheckConstraint(
                condition=models.Q(
                    minimum_score__lte=models.F(
                        "maximum_score"
                    )
                ),
                name="grade_minimum_not_above_maximum",
            ),
        ]

    def clean(self):
        errors = {}

        if (
            self.grade_scale_id
            and self.school_id
            and self.grade_scale.school_id != self.school_id
        ):
            errors["grade_scale"] = (
                "Grade scale belongs to another school."
            )

        if self.grade_scale_id:

            overlaps = GradeBand.objects.filter(
                grade_scale=self.grade_scale,
                minimum_score__lte=self.maximum_score,
                maximum_score__gte=self.minimum_score,
            )

            if self.pk:
                overlaps = overlaps.exclude(
                    pk=self.pk
                )

            if overlaps.exists():
                errors["minimum_score"] = (
                    "This grade range overlaps "
                    "with another grade band."
                )

        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return (
            f"{self.grade}: "
            f"{self.minimum_score}-"
            f"{self.maximum_score}"
        )


class OfferingAssessmentPlan(SchoolOwnedModel):
    """
    Connects:

    Subject Offering
    +
    Term
    +
    Assessment Scheme
    +
    Grade Scale
    """

    offering = models.ForeignKey(
        "academics.SubjectOffering",
        on_delete=models.CASCADE,
        related_name="assessment_plans",
    )

    term = models.ForeignKey(
        "academics.Term",
        on_delete=models.PROTECT,
        related_name="assessment_plans",
    )

    scheme = models.ForeignKey(
        AssessmentScheme,
        on_delete=models.PROTECT,
        related_name="offering_plans",
    )

    grade_scale = models.ForeignKey(
        GradeScale,
        on_delete=models.PROTECT,
        related_name="offering_plans",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "offering",
                    "term",
                ],
                name=(
                    "one_assessment_plan_"
                    "per_offering_term"
                ),
            ),
        ]

    def clean(self):
        errors = {}

        objects = [
            ("offering", self.offering),
            ("term", self.term),
            ("scheme", self.scheme),
            ("grade_scale", self.grade_scale),
        ]

        for field_name, obj in objects:
            if (
                obj
                and self.school_id
                and obj.school_id != self.school_id
            ):
                errors[field_name] = (
                    f"{field_name.replace('_', ' ').title()} "
                    "belongs to another school."
                )

        if (
            self.offering_id
            and self.term_id
            and self.offering.academic_year_id
            != self.term.academic_year_id
        ):
            errors["term"] = (
                "Term and subject offering must belong "
                "to the same academic year."
            )

        if (
            self.scheme_id
            and self.term_id
            and self.scheme.academic_year_id
            != self.term.academic_year_id
        ):
            errors["scheme"] = (
                "Assessment scheme belongs to a different "
                "academic year."
            )

        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return (
            f"{self.offering} - "
            f"{self.term.name}"
        )


class Assessment(SchoolOwnedModel):

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        OPEN = "open", "Open"
        CLOSED = "closed", "Closed"
        LOCKED = "locked", "Locked"

    assessment_plan = models.ForeignKey(
        OfferingAssessmentPlan,
        on_delete=models.CASCADE,
        related_name="assessments",
    )

    category = models.ForeignKey(
        AssessmentCategory,
        on_delete=models.PROTECT,
        related_name="assessments",
    )

    name = models.CharField(
        max_length=150,
    )

    max_score = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        default=100,
    )

    assessment_date = models.DateField(
        null=True,
        blank=True,
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "assessment_plan",
                    "category",
                    "name",
                ],
                name=(
                    "unique_assessment_name_"
                    "per_plan_category"
                ),
            ),

            models.CheckConstraint(
                condition=models.Q(
                    max_score__gt=0
                ),
                name="assessment_max_score_positive",
            ),
        ]

    def clean(self):
        errors = {}

        if (
            self.assessment_plan_id
            and self.school_id
            and self.assessment_plan.school_id
            != self.school_id
        ):
            errors["assessment_plan"] = (
                "Assessment plan belongs to another school."
            )

        if (
            self.category_id
            and self.school_id
            and self.category.school_id
            != self.school_id
        ):
            errors["category"] = (
                "Category belongs to another school."
            )

        if (
            self.assessment_plan_id
            and self.category_id
            and self.category.scheme_id
            != self.assessment_plan.scheme_id
        ):
            errors["category"] = (
                "Assessment category does not belong "
                "to this assessment scheme."
            )

        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return self.name


class Score(SchoolOwnedModel):

    assessment = models.ForeignKey(
        Assessment,
        on_delete=models.CASCADE,
        related_name="scores",
    )

    enrollment = models.ForeignKey(
        "academics.Enrollment",
        on_delete=models.PROTECT,
        related_name="assessment_scores",
    )

    raw_score = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        null=True,
        blank=True,
    )

    is_absent = models.BooleanField(
        default=False,
    )

    comment = models.CharField(
        max_length=255,
        blank=True,
    )

    entered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="scores_entered",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "assessment",
                    "enrollment",
                ],
                name=(
                    "one_score_per_student_"
                    "assessment"
                ),
            ),

            models.CheckConstraint(
                condition=(
                    models.Q(raw_score__isnull=True)
                    | models.Q(raw_score__gte=0)
                ),
                name="score_not_negative",
            ),
        ]

    def clean(self):
        errors = {}

        if (
            self.assessment_id
            and self.school_id
            and self.assessment.school_id
            != self.school_id
        ):
            errors["assessment"] = (
                "Assessment belongs to another school."
            )

        if (
            self.enrollment_id
            and self.school_id
            and self.enrollment.school_id
            != self.school_id
        ):
            errors["enrollment"] = (
                "Enrollment belongs to another school."
            )

        if self.assessment_id and self.enrollment_id:

            offering = (
                self.assessment
                .assessment_plan
                .offering
            )

            if (
                self.enrollment.academic_year_id
                != offering.academic_year_id
            ):
                errors["enrollment"] = (
                    "Student is not enrolled in this academic year."
                )

            if (
                self.enrollment.class_section_id
                != offering.class_section_id
            ):
                errors["enrollment"] = (
                    "Student is not enrolled in this class."
                )

        if self.is_absent and self.raw_score is not None:
            errors["raw_score"] = (
                "An absent student should not have a raw score."
            )

        if (
            not self.is_absent
            and self.raw_score is None
        ):
            errors["raw_score"] = (
                "Enter a score or mark the student absent."
            )

        if (
            self.raw_score is not None
            and self.assessment_id
            and self.raw_score > self.assessment.max_score
        ):
            errors["raw_score"] = (
                f"Score cannot exceed "
                f"{self.assessment.max_score}."
            )

        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return (
            f"{self.enrollment.student} - "
            f"{self.assessment}"
        )


class SubjectResult(SchoolOwnedModel):

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        SUBMITTED = "submitted", "Submitted"
        APPROVED = "approved", "Approved"
        PUBLISHED = "published", "Published"

    assessment_plan = models.ForeignKey(
        OfferingAssessmentPlan,
        on_delete=models.PROTECT,
        related_name="results",
    )

    enrollment = models.ForeignKey(
        "academics.Enrollment",
        on_delete=models.PROTECT,
        related_name="subject_results",
    )

    total_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
    )

    grade = models.CharField(
        max_length=20,
    )

    grade_label = models.CharField(
        max_length=100,
        blank=True,
    )

    remark = models.CharField(
        max_length=150,
        blank=True,
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
    )

    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="results_submitted",
    )

    submitted_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="results_approved",
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
        related_name="results_published",
    )

    published_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "assessment_plan",
                    "enrollment",
                ],
                name=(
                    "one_subject_result_per_"
                    "student_plan"
                ),
            ),

            models.CheckConstraint(
                condition=(
                    models.Q(total_score__gte=0)
                    & models.Q(total_score__lte=100)
                ),
                name="subject_result_score_0_to_100",
            ),
        ]

    def __str__(self):
        return (
            f"{self.enrollment.student} - "
            f"{self.assessment_plan.offering.subject} "
            f"{self.total_score}"
        )