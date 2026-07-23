from django.contrib.auth.models import Permission

from .models import SchoolMembership


def get_active_membership(
    *,
    user,
    school,
):
    """
    Return the user's active membership
    for a specific school.
    """

    if (
        not user
        or not user.is_authenticated
        or not school
    ):
        return None

    return (
        SchoolMembership.objects
        .filter(
            user=user,
            school=school,
            is_active=True,
        )
        .prefetch_related(
            "roles__permissions"
        )
        .first()
    )


def get_school_permissions(
    *,
    user,
    school,
):
    """
    Return permission strings such as:

    students.view_student
    finance.record_student_payment
    assessments.approve_subject_result
    """

    if (
        user.is_superuser
        or user.is_platform_admin
    ):
        return set(
            Permission.objects.values_list(
                "content_type__app_label",
                "codename",
            )
        )

    membership = get_active_membership(
        user=user,
        school=school,
    )

    if not membership:
        return set()

    permissions = (
        Permission.objects
        .filter(
            school_roles__memberships=membership
        )
        .values_list(
            "content_type__app_label",
            "codename",
        )
        .distinct()
    )

    return {
        f"{app_label}.{codename}"
        for app_label, codename
        in permissions
    }


def has_school_permission(
    *,
    user,
    school,
    permission,
):
    # has_school_permission(
    #     user=request.user,
    #     school=request.school,
    #     permission=(
    #         "assessments.approve_subject_result"
    #     ),
    # )

    if not user.is_authenticated:
        return False

    if (
        user.is_superuser
        or user.is_platform_admin
    ):
        return True

    return permission in get_school_permissions(
        user=user,
        school=school,
    )


def has_any_school_permission(
    *,
    user,
    school,
    permissions,
):
    user_permissions = get_school_permissions(
        user=user,
        school=school,
    )

    return bool(
        user_permissions.intersection(
            permissions
        )
    )


def has_role(
    *,
    user,
    school,
    role_code,
):
    membership = get_active_membership(
        user=user,
        school=school,
    )

    if not membership:
        return False

    return membership.roles.filter(
        code=role_code,
    ).exists()