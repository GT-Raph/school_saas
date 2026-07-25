from django.core.exceptions import PermissionDenied

from apps.academics.models import (
    Enrollment,
    SubjectOffering,
    TeacherAssignment,
)
from apps.staff.models import Staff


def get_teacher_profile(
    *,
    user,
    school,
):
    staff = (
        Staff.objects
        .for_school(school)
        .filter(
            user=user,
            is_teacher=True,
            employment_status=(
                Staff.EmploymentStatus.ACTIVE
            ),
        )
        .first()
    )

    if not staff:
        raise PermissionDenied(
            (
                "No active teacher profile "
                "is linked to this account."
            )
        )

    return staff


def get_teacher_offering_or_403(
    *,
    user,
    school,
    offering_id,
):
    teacher = get_teacher_profile(
        user=user,
        school=school,
    )

    assignment = (
        TeacherAssignment.objects
        .for_school(school)
        .filter(
            teacher=teacher,
            offering_id=offering_id,
            is_active=True,
        )
        .select_related(
            "offering__subject",
            "offering__class_section__level",
            "offering__academic_year",
        )
        .first()
    )

    if not assignment:
        raise PermissionDenied(
            (
                "You are not assigned to "
                "this class and subject."
            )
        )

    return teacher, assignment.offering


def get_offering_enrollments(
    *,
    offering,
):
    return (
        Enrollment.objects
        .for_school(
            offering.school
        )
        .filter(
            academic_year=(
                offering.academic_year
            ),
            class_section=(
                offering.class_section
            ),
            status=(
                Enrollment.Status.ACTIVE
            ),
        )
        .select_related(
            "student"
        )
        .order_by(
            "student__last_name",
            "student__first_name",
        )
    )