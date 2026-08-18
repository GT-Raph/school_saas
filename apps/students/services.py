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

from .models import (
    Student,
    StudentAdmissionSequence,
)

import re

from django.utils import timezone

from apps.schools.models import School


def _derive_admission_prefix(
    school,
):
    words = re.findall(
        r"[A-Za-z0-9]+",
        school.name,
    )

    if len(words) >= 2:
        prefix = "".join(
            word[0]
            for word in words
        )
    elif words:
        prefix = words[0][:3]
    else:
        prefix = "STD"

    return prefix.upper()[:10]


def _existing_max_sequence(
    *,
    school,
    prefix,
    year,
):
    start = (
        f"{prefix}-{year}-"
    )

    admission_numbers = (
        Student.objects
        .for_school(school)
        .filter(
            admission_number__startswith=start
        )
        .values_list(
            "admission_number",
            flat=True,
        )
    )

    maximum = 0

    for admission_number in (
        admission_numbers
    ):
        suffix = (
            admission_number[
                len(start):
            ]
        )

        if suffix.isdigit():
            maximum = max(
                maximum,
                int(suffix),
            )

    return maximum


@transaction.atomic
def generate_admission_number(
    *,
    school,
    admission_date=None,
    academic_year=None,
):
    locked_school = (
        School.objects
        .select_for_update()
        .get(
            pk=school.pk
        )
    )

    prefix = (
        locked_school
        .admission_prefix
        .strip()
        .upper()
    )

    if not prefix:
        prefix = (
            _derive_admission_prefix(
                locked_school
            )
        )

        locked_school.admission_prefix = (
            prefix
        )

        locked_school.save(
            update_fields=[
                "admission_prefix",
                "updated_at",
            ]
        )

    if admission_date:
        year = admission_date.year

    elif academic_year:
        year = (
            academic_year
            .starts_on
            .year
        )

    else:
        year = (
            timezone.localdate()
            .year
        )

    existing_max = (
        _existing_max_sequence(
            school=locked_school,
            prefix=prefix,
            year=year,
        )
    )

    sequence, created = (
        StudentAdmissionSequence
        .objects
        .get_or_create(
            school=locked_school,
            year=year,
            defaults={
                "last_number":
                    existing_max,
            },
        )
    )

    if (
        not created
        and sequence.last_number
        < existing_max
    ):
        sequence.last_number = (
            existing_max
        )

    sequence.last_number += 1

    sequence.save(
        update_fields=[
            "last_number",
            "updated_at",
        ]
    )

    return (
        f"{prefix}-"
        f"{year}-"
        f"{sequence.last_number:04d}"
    )

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
            generate_admission_number(
                school=school,
                admission_date=(
                    data.get(
                        "admission_date"
                    )
                ),
                academic_year=(
                    data.get(
                        "academic_year"
                    )
                ),
            )
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