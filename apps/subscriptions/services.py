from django.core.exceptions import ValidationError

from apps.academics.models import Enrollment

from .models import SchoolSubscription


def get_active_student_count(
    *,
    school,
):
    """
    Billable active students are based on
    current-year ACTIVE enrollments.

    Historical students do not count.
    """

    return (
        Enrollment.objects
        .for_school(school)
        .filter(
            academic_year__is_current=True,
            status=Enrollment.Status.ACTIVE,
        )
        .values(
            "student_id"
        )
        .distinct()
        .count()
    )


def get_subscription_usage(
    *,
    school,
):
    try:
        subscription = (
            school.subscription
        )

    except SchoolSubscription.DoesNotExist:

        return {
            "subscription": None,
            "active_students": (
                get_active_student_count(
                    school=school
                )
            ),
            "student_limit": None,
            "remaining": None,
        }

    active = get_active_student_count(
        school=school
    )

    limit = (
        subscription.plan
        .active_student_limit
    )

    return {
        "subscription": subscription,
        "active_students": active,
        "student_limit": limit,
        "remaining": max(
            limit - active,
            0,
        ),
    }


def assert_can_add_active_students(
    *,
    school,
    additional_count=1,
):
    try:
        subscription = (
            school.subscription
        )

    except SchoolSubscription.DoesNotExist:

        raise ValidationError(
            "This school does not have "
            "a configured subscription."
        )

    if not subscription.can_write:

        raise ValidationError(
            "This subscription is currently "
            "read-only or suspended."
        )

    current = get_active_student_count(
        school=school
    )

    limit = (
        subscription.plan
        .active_student_limit
    )

    projected = (
        current
        + additional_count
    )

    if projected > limit:

        raise ValidationError(
            (
                f"This operation would increase "
                f"active enrollment to {projected}, "
                f"but the current plan allows "
                f"only {limit} active students."
            )
        )

    return True