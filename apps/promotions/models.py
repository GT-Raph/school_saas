from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from apps.core.models import SchoolOwnedModel


class PromotionPolicy(SchoolOwnedModel):
    """
    Versioned promotion policy for a class level.

    Example:

    Basic 4 - 2026/2027

    Minimum average: 50%
    Subject pass mark: 50%
    Maximum failed subjects: 2
    Minimum attendance: 75%
    """

    class FailureAction(
        models.TextChoices
    ):
        REPEAT = "repeat", "Repeat"
        REVIEW = "review", "Manual Review"

    name = models.CharField(
        max_length=150,
    )

    academic_year = models.ForeignKey(
        "academics.AcademicYear",
        on_delete=models.PROTECT,
        related_name="promotion_policies",
    )

    class_level = models.ForeignKey(
        "academics.ClassLevel",
        on_delete=models.PROTECT,
        related_name="promotion_policies",
    )

    version = models.PositiveIntegerField(
        default=1,
    )

    minimum_overall_average = (
        models.DecimalField(
            max_digits=5,
            decimal_places=2,
            default=50,
        )
    )

    subject_pass_mark = (
        models.DecimalField(
            max_digits=5,
            decimal_places=2,
            default=50,
        )
    )

    maximum_failed_subjects = (
        models.PositiveSmallIntegerField(
            default=2,
        )
    )

    minimum_attendance_percentage = (
        models.DecimalField(
            max_digits=5,
            decimal_places=2,
            null=True,
            blank=True,
            default=75,
        )
    )

    demotion_threshold = (
        models.DecimalField(
            max_digits=5,
            decimal_places=2,
            null=True,
            blank=True,
            help_text=(
                "Optional. If the annual average "
                "falls below this value, the system "
                "may recommend demotion."
            ),
        )
    )

    failure_action = models.CharField(
        max_length=20,
        choices=FailureAction.choices,
        default=FailureAction.REPEAT,
    )

    require_all_terms = models.BooleanField(
        default=True,
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
                    "class_level",
                    "version",
                ],
                name=(
                    "unique_promotion_policy_"
                    "version"
                ),
            ),

            models.UniqueConstraint(
                fields=[
                    "school",
                    "academic_year",
                    "class_level",
                ],
                condition=models.Q(
                    is_active=True
                ),
                name=(
                    "one_active_promotion_policy_"
                    "per_level_year"
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

        if (
            self.class_level_id
            and self.school_id
            and self.class_level.school_id
            != self.school_id
        ):
            errors["class_level"] = (
                "Class level belongs "
                "to another school."
            )

        if (
            self.demotion_threshold
            is not None
            and self.demotion_threshold
            >= self.minimum_overall_average
        ):
            errors[
                "demotion_threshold"
            ] = (
                "Demotion threshold should "
                "be lower than the normal "
                "promotion average."
            )

        if errors:
            raise ValidationError(
                errors
            )

    def __str__(self):
        return (
            f"{self.name} "
            f"v{self.version}"
        )


class PromotionSubjectRule(
    SchoolOwnedModel
):
    """
    Special rule for an important subject.

    Example:
        Mathematics minimum 45%
        English minimum 45%
    """

    policy = models.ForeignKey(
        PromotionPolicy,
        on_delete=models.CASCADE,
        related_name="subject_rules",
    )

    subject = models.ForeignKey(
        "academics.Subject",
        on_delete=models.PROTECT,
        related_name="promotion_rules",
    )

    minimum_average = (
        models.DecimalField(
            max_digits=5,
            decimal_places=2,
        )
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "policy",
                    "subject",
                ],
                name=(
                    "unique_promotion_subject_"
                    "rule"
                ),
            ),
        ]

    def clean(self):
        errors = {}

        if (
            self.policy_id
            and self.school_id
            and self.policy.school_id
            != self.school_id
        ):
            errors["policy"] = (
                "Policy belongs to "
                "another school."
            )

        if (
            self.subject_id
            and self.school_id
            and self.subject.school_id
            != self.school_id
        ):
            errors["subject"] = (
                "Subject belongs to "
                "another school."
            )

        if errors:
            raise ValidationError(
                errors
            )

    def __str__(self):
        return (
            f"{self.subject} >= "
            f"{self.minimum_average}%"
        )


class PromotionEvaluation(
    SchoolOwnedModel
):

    class Recommendation(
        models.TextChoices
    ):
        PROMOTE = (
            "promote",
            "Promote",
        )

        REPEAT = (
            "repeat",
            "Repeat",
        )

        DEMOTE = (
            "demote",
            "Demote",
        )

        REVIEW = (
            "review",
            "Manual Review",
        )

        GRADUATE = (
            "graduate",
            "Graduate",
        )

    policy = models.ForeignKey(
        PromotionPolicy,
        on_delete=models.PROTECT,
        related_name="evaluations",
    )

    enrollment = models.ForeignKey(
        "academics.Enrollment",
        on_delete=models.PROTECT,
        related_name=(
            "promotion_evaluations"
        ),
    )

    annual_average = (
        models.DecimalField(
            max_digits=5,
            decimal_places=2,
            null=True,
            blank=True,
        )
    )

    attendance_percentage = (
        models.DecimalField(
            max_digits=5,
            decimal_places=2,
            null=True,
            blank=True,
        )
    )

    failed_subjects = (
        models.PositiveSmallIntegerField(
            default=0,
        )
    )

    recommendation = models.CharField(
        max_length=20,
        choices=Recommendation.choices,
    )

    reasons = models.JSONField(
        default=list,
    )

    metrics = models.JSONField(
        default=dict,
    )

    evaluated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "policy",
                    "enrollment",
                ],
                name=(
                    "one_promotion_evaluation_"
                    "per_policy_enrollment"
                ),
            ),
        ]
        
        permissions = [
            (
                "run_promotion_evaluation",
                "Can run promotion evaluation",
            ),
        ]

    def __str__(self):
        return (
            f"{self.enrollment.student} - "
            f"{self.recommendation}"
        )


class PromotionDecision(
    SchoolOwnedModel
):

    class Decision(
        models.TextChoices
    ):
        PROMOTE = (
            "promote",
            "Promote",
        )

        REPEAT = (
            "repeat",
            "Repeat",
        )

        DEMOTE = (
            "demote",
            "Demote",
        )

        GRADUATE = (
            "graduate",
            "Graduate",
        )

        REVIEW = (
            "review",
            "Manual Review",
        )

    evaluation = models.OneToOneField(
        PromotionEvaluation,
        on_delete=models.PROTECT,
        related_name="decision",
    )

    final_decision = models.CharField(
        max_length=20,
        choices=Decision.choices,
    )

    target_class_section = (
        models.ForeignKey(
            "academics.ClassSection",
            on_delete=models.PROTECT,
            null=True,
            blank=True,
            related_name=(
                "promotion_decisions_targeting"
            ),
        )
    )

    reason = models.TextField(
        blank=True,
    )

    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name=(
            "promotion_decisions_approved"
        ),
    )

    approved_at = models.DateTimeField()

    executed_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    resulting_enrollment = (
        models.OneToOneField(
            "academics.Enrollment",
            on_delete=models.SET_NULL,
            null=True,
            blank=True,
            related_name=(
                "source_promotion_decision"
            ),
        )
    )

    def clean(self):
        errors = {}

        if (
            self.evaluation_id
            and self.school_id
            and self.evaluation.school_id
            != self.school_id
        ):
            errors["evaluation"] = (
                "Evaluation belongs "
                "to another school."
            )

        if (
            self.target_class_section_id
            and self.school_id
            and self.target_class_section
            .school_id
            != self.school_id
        ):
            errors[
                "target_class_section"
            ] = (
                "Target class belongs "
                "to another school."
            )

        if errors:
            raise ValidationError(
                errors
            )
        
    class Meta:
        permissions = [
            (
                "approve_promotion_decision",
                "Can approve promotion decisions",
            ),
            (
                "execute_promotion_decision",
                "Can execute promotion decisions",
            ),
        ]

    def __str__(self):
        return (
            f"{self.evaluation.enrollment.student} "
            f"- {self.final_decision}"
        )