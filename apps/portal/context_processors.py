from apps.schools.permissions import (
    get_school_permissions,
    has_role,
)


def portal_access(
    request,
):
    if (
        not hasattr(
            request,
            "school",
        )
        or not request.school
        or not request.user
        .is_authenticated
    ):
        return {}

    permissions = (
        get_school_permissions(
            user=request.user,
            school=request.school,
        )
    )

    def allowed(
        permission,
    ):
        if (
            request.user.is_superuser
            or request.user
            .is_platform_admin
        ):
            return True

        return (
            permission
            in permissions
        )

    return {
        "portal_access": {

            "academic": (
                allowed(
                    "assessments.approve_subject_result"
                )
                or allowed(
                    "reports.view_termresult"
                )
            ),

            "users":
                allowed(
                    "schools.manage_school_users"
                ),

            "students":
                allowed(
                    "students.view_student"
                ),

            "guardians":
                allowed(
                    "guardians.view_guardian"
                ),

            "staff":
                allowed(
                    "staff.view_staff"
                ),

            "finance":
                allowed(
                    "finance.view_studentinvoice"
                ),

            "teacher":
                has_role(
                    user=request.user,
                    school=request.school,
                    role_code="teacher",
                ),

            "settings":
                allowed(
                    (
                        "schools."
                        "manage_school_settings"
                    )
                ),
        }
    }