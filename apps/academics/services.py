from django.db import transaction

from .models import Enrollment


@transaction.atomic
def enroll_student(
    *,
    school,
    student,
    academic_year,
    class_section,
    enrolled_on,
    roll_number="",
    notes="",
):
    """
    Create a validated student enrollment.

    Critical business operations should call this service
    rather than creating Enrollment records directly.
    """

    enrollment = Enrollment(
        school=school,
        student=student,
        academic_year=academic_year,
        class_section=class_section,
        enrolled_on=enrolled_on,
        roll_number=roll_number,
        notes=notes,
    )

    enrollment.full_clean()

    enrollment.save()

    return enrollment