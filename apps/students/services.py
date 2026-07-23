from django.db import transaction

from apps.academics.services import (
    enroll_student,
)
from apps.audit.models import (
    AuditEvent,
)
from apps.guardians.models import (
    Guardian,
    StudentGuardian,
)
from apps.guardians.services import (
    link_guardian_to_student,
)
from apps.subscriptions.services import (
    assert_can_add_active_students,
)

from .models import Student


@transaction.atomic
def admit_student(
    *,
    school,
    data,
    created_by,
):
    assert_can_add_active_students(
        school=school,
        additional_count=1,
    )

    student = Student(
        school=school,

        admission_number=(
            data[
                "admission_number"
            ]
        ),

        first_name=(
            data[
                "first_name"
            ]
        ),

        middle_name=(
            data.get(
                "middle_name",
                "",
            )
        ),

        last_name=(
            data[
                "last_name"
            ]
        ),

        date_of_birth=(
            data.get(
                "date_of_birth"
            )
        ),

        gender=(
            data[
                "gender"
            ]
        ),

        admission_date=(
            data[
                "admission_date"
            ]
        ),

        phone_number=(
            data.get(
                "phone_number",
                "",
            )
        ),

        email=(
            data.get(
                "email",
                "",
            )
        ),

        status=(
            Student.Status.ACTIVE
        ),
    )

    student.full_clean()
    student.save()

    enrollment = enroll_student(
        school=school,

        student=student,

        academic_year=(
            data[
                "academic_year"
            ]
        ),

        class_section=(
            data[
                "class_section"
            ]
        ),

        enrolled_on=(
            data[
                "enrolled_on"
            ]
        ),
    )

    guardian_first_name = (
        data.get(
            "guardian_first_name"
        )
    )

    guardian = None

    if guardian_first_name:

        guardian_phone = (
            data[
                "guardian_phone"
            ]
        )

        guardian = (
            Guardian.objects
            .for_school(school)
            .filter(
                first_name__iexact=(
                    guardian_first_name
                ),

                last_name__iexact=(
                    data[
                        "guardian_last_name"
                    ]
                ),

                phone_number=(
                    guardian_phone
                ),
            )
            .first()
        )

        if not guardian:

            guardian = Guardian(
                school=school,

                first_name=(
                    guardian_first_name
                ),

                last_name=(
                    data[
                        "guardian_last_name"
                    ]
                ),

                phone_number=(
                    guardian_phone
                ),

                email=(
                    data.get(
                        "guardian_email",
                        "",
                    )
                ),
            )

            guardian.full_clean()
            guardian.save()

        link_guardian_to_student(
            school=school,

            student=student,

            guardian=guardian,

            relationship=(
                data.get(
                    "guardian_relationship"
                )
                or StudentGuardian
                .Relationship.GUARDIAN
            ),

            is_primary_contact=True,

            receives_reports=True,

            emergency_contact=True,
        )

    AuditEvent.objects.create(
        school=school,

        actor=created_by,

        action=(
            "student_admitted"
        ),

        object_type="Student",

        object_id=str(
            student.id
        ),

        changes={
            "admission_number": (
                student.admission_number
            ),

            "name": (
                student.full_name
            ),

            "academic_year": (
                enrollment
                .academic_year.name
            ),

            "class": str(
                enrollment
                .class_section
            ),
        },
    )

    return student