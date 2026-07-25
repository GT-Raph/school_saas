from django.db import transaction

from .models import StudentGuardian


@transaction.atomic
def link_guardian_to_student(
    *,
    school,
    student,
    guardian,
    relationship,
    is_primary_contact=False,
    financially_responsible=False,
    receives_reports=True,
    emergency_contact=False,
    can_collect_student=False,
):
    link = StudentGuardian(
        school=school,
        student=student,
        guardian=guardian,
        relationship=relationship,
        is_primary_contact=(
            is_primary_contact
        ),
        financially_responsible=(
            financially_responsible
        ),
        receives_reports=(
            receives_reports
        ),
        emergency_contact=(
            emergency_contact
        ),
        can_collect_student=(
            can_collect_student
        ),
    )

    link.full_clean()

    link.save()

    return link