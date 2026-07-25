from django.core.exceptions import PermissionDenied

from apps.guardians.models import Guardian
from apps.students.models import Student


def get_guardian_or_403(
    *,
    user,
    school,
):
    guardian = (
        Guardian.objects
        .for_school(school)
        .filter(
            user=user,
            is_active=True,
        )
        .first()
    )

    if not guardian:

        raise PermissionDenied(
            "No guardian profile found."
        )

    return guardian


def get_parent_student_or_403(
    *,
    user,
    school,
    student_id,
):
    guardian = get_guardian_or_403(
        user=user,
        school=school,
    )

    link = (
        guardian.student_links
        .filter(
            school=school,
            student_id=student_id,
        )
        .select_related(
            "student"
        )
        .first()
    )

    if not link:

        raise PermissionDenied(
            (
                "You do not have access "
                "to this student."
            )
        )

    return guardian, link.student


def get_student_or_403(
    *,
    user,
    school,
):
    student = (
        Student.objects
        .for_school(school)
        .filter(
            user=user
        )
        .first()
    )

    if not student:

        raise PermissionDenied(
            "No student profile found."
        )

    return student