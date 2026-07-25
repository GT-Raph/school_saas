from apps.schools.permissions import (
    has_any_school_permission,
    has_role,
)


def determine_dashboard(
    *,
    user,
    school,
):
    """
    Priority matters.

    A school administrator may also
    technically be a teacher, so the
    most privileged operational dashboard
    is resolved first.
    """

    if (
        user.is_superuser
        or user.is_platform_admin
    ):
        return "school_admin"

    if has_role(
        user=user,
        school=school,
        role_code="school-admin",
    ):
        return "school_admin"

    if has_role(
        user=user,
        school=school,
        role_code="academic-admin",
    ):
        return "academic"

    if has_role(
        user=user,
        school=school,
        role_code="finance",
    ):
        return "finance"

    if has_role(
        user=user,
        school=school,
        role_code="teacher",
    ):
        return "teacher"

    if has_role(
        user=user,
        school=school,
        role_code="parent",
    ):
        return "parent"

    if has_role(
        user=user,
        school=school,
        role_code="student",
    ):
        return "student"

    return "basic"