from django.core.exceptions import ValidationError
from django.db import transaction

from apps.accounts.models import User
from apps.audit.models import AuditEvent
from apps.schools.models import SchoolMembership


@transaction.atomic
def create_school_user(
    *,
    school,
    data,
    created_by,
):
    username = data[
        "username"
    ]

    if User.objects.filter(
        username=username
    ).exists():

        raise ValidationError(
            (
                "This username is already "
                "in use."
            )
        )

    user = User.objects.create_user(
        username=username,

        first_name=data[
            "first_name"
        ],

        last_name=data[
            "last_name"
        ],

        email=data.get(
            "email",
            "",
        ),

        password=data[
            "temporary_password"
        ],

        must_change_password=True,
    )

    membership = (
        SchoolMembership.objects.create(
            user=user,
            school=school,
            is_active=True,
        )
    )

    role = data[
        "role"
    ]

    membership.roles.add(
        role
    )

    staff = data.get(
        "staff_profile"
    )

    guardian = data.get(
        "guardian_profile"
    )

    student = data.get(
        "student_profile"
    )

    if staff:

        if (
            staff.school_id
            != school.id
        ):
            raise ValidationError(
                "Invalid staff profile."
            )

        staff.user = user
        staff.full_clean()
        staff.save()

    if guardian:

        if (
            guardian.school_id
            != school.id
        ):
            raise ValidationError(
                "Invalid guardian profile."
            )

        guardian.user = user
        guardian.full_clean()
        guardian.save()

    if student:

        if (
            student.school_id
            != school.id
        ):
            raise ValidationError(
                "Invalid student profile."
            )

        student.user = user
        student.full_clean()
        student.save()

    AuditEvent.objects.create(
        school=school,
        actor=created_by,

        action=(
            "school_user_created"
        ),

        object_type=(
            "SchoolMembership"
        ),

        object_id=str(
            membership.id
        ),

        changes={
            "username":
                user.username,

            "role":
                role.code,

            "linked_staff":
                str(
                    staff.id
                )
                if staff
                else None,

            "linked_guardian":
                str(
                    guardian.id
                )
                if guardian
                else None,

            "linked_student":
                str(
                    student.id
                )
                if student
                else None,
        },
    )

    return membership