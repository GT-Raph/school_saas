from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from .models import (
    GradeBand,
    Score,
    SubjectResult,
)


def validate_scheme_weights(scheme):
    """
    Assessment category weights must total exactly 100%.
    """

    total = (
        scheme.categories.aggregate(
            total=Sum("weight")
        )["total"]
        or Decimal("0")
    )

    if total != Decimal("100"):
        raise ValidationError(
            f"Assessment category weights must total "
            f"100%. Current total: {total}%."
        )

    return True


def find_grade_band(
    *,
    grade_scale,
    percentage,
):
    band = (
        GradeBand.objects
        .filter(
            grade_scale=grade_scale,
            minimum_score__lte=percentage,
            maximum_score__gte=percentage,
        )
        .order_by("-minimum_score")
        .first()
    )

    if not band:
        raise ValidationError(
            f"No grade band exists for score "
            f"{percentage}."
        )

    return band


@transaction.atomic
def save_student_score(
    *,
    school,
    assessment,
    enrollment,
    raw_score=None,
    is_absent=False,
    comment="",
    entered_by=None,
):
    if assessment.status == assessment.Status.LOCKED:
        raise ValidationError(
            "This assessment is locked."
        )

    score, _ = Score.objects.get_or_create(
        assessment=assessment,
        enrollment=enrollment,
        defaults={
            "school": school,
        },
    )

    score.school = school
    score.raw_score = raw_score
    score.is_absent = is_absent
    score.comment = comment
    score.entered_by = entered_by

    score.full_clean()
    score.save()

    return score


@transaction.atomic
def calculate_subject_result(
    *,
    assessment_plan,
    enrollment,
):
    """
    Calculation method:

    For each category:

        total earned
        ----------------  x category weight
        total possible

    Then add all category contributions.

    Example:

    Classwork = 30%
    Quiz      = 10%
    Exam      = 60%
    """

    validate_scheme_weights(
        assessment_plan.scheme
    )

    total_percentage = Decimal("0")

    categories = (
        assessment_plan.scheme.categories.all()
        .order_by("sequence")
    )

    for category in categories:

        assessments = (
            assessment_plan.assessments
            .filter(
                category=category,
            )
            .exclude(
                status="draft",
            )
        )

        if not assessments.exists():
            raise ValidationError(
                f"No assessment exists for "
                f"category '{category.name}'."
            )

        possible = Decimal("0")
        earned = Decimal("0")

        for assessment in assessments:

            try:
                score = assessment.scores.get(
                    enrollment=enrollment
                )

            except Score.DoesNotExist:
                raise ValidationError(
                    f"Missing score for "
                    f"{assessment.name}."
                )

            possible += assessment.max_score

            if score.is_absent:
                earned += Decimal("0")
            else:
                earned += score.raw_score

        if possible <= 0:
            raise ValidationError(
                f"Invalid total possible score "
                f"for category '{category.name}'."
            )

        category_percentage = (
            earned / possible
        ) * category.weight

        total_percentage += category_percentage

    total_percentage = total_percentage.quantize(
        Decimal("0.01")
    )

    band = find_grade_band(
        grade_scale=assessment_plan.grade_scale,
        percentage=total_percentage,
    )

    result, _ = SubjectResult.objects.update_or_create(
        assessment_plan=assessment_plan,
        enrollment=enrollment,
        defaults={
            "school": assessment_plan.school,
            "total_score": total_percentage,
            "grade": band.grade,
            "is_pass": band.is_pass,
            "grade_label": band.label,
            "remark": band.remark,
        },
    )

    result.full_clean()
    result.save()

    return result


@transaction.atomic
def submit_result(
    *,
    result,
    user,
):
    if result.status != SubjectResult.Status.DRAFT:
        raise ValidationError(
            "Only draft results can be submitted."
        )

    result.status = SubjectResult.Status.SUBMITTED
    result.submitted_by = user
    result.submitted_at = timezone.now()

    result.save(
        update_fields=[
            "status",
            "submitted_by",
            "submitted_at",
            "updated_at",
        ]
    )

    return result


@transaction.atomic
def approve_result(
    *,
    result,
    user,
):
    if (
        result.status
        != SubjectResult.Status.SUBMITTED
    ):
        raise ValidationError(
            "Only submitted results can be approved."
        )

    result.status = SubjectResult.Status.APPROVED
    result.approved_by = user
    result.approved_at = timezone.now()

    result.save(
        update_fields=[
            "status",
            "approved_by",
            "approved_at",
            "updated_at",
        ]
    )

    return result


@transaction.atomic
def publish_result(
    *,
    result,
    user,
):
    if (
        result.status
        != SubjectResult.Status.APPROVED
    ):
        raise ValidationError(
            "Only approved results can be published."
        )

    result.status = SubjectResult.Status.PUBLISHED
    result.published_by = user
    result.published_at = timezone.now()

    result.save(
        update_fields=[
            "status",
            "published_by",
            "published_at",
            "updated_at",
        ]
    )

    return result