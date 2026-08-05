import re

from django.core.exceptions import ObjectDoesNotExist

from apps.schools.permissions import (
    get_school_permissions,
    has_role,
)


HEX_COLOR_PATTERN = re.compile(
    r"^#[0-9A-Fa-f]{6}$"
)


def safe_color(
    value,
    fallback,
):
    value = str(
        value or ""
    ).strip()

    if HEX_COLOR_PATTERN.fullmatch(
        value
    ):
        return value

    return fallback


def portal_access(
    request,
):
    school = getattr(
        request,
        "school",
        None,
    )

    user = getattr(
        request,
        "user",
        None,
    )

    if (
        not school
        or not user
        or not user.is_authenticated
    ):
        return {
            "portal_access": {},
        }

    permissions = get_school_permissions(
        user=user,
        school=school,
    )

    unrestricted = (
        user.is_superuser
        or user.is_platform_admin
    )

    def allowed(
        permission,
    ):
        return (
            unrestricted
            or permission in permissions
        )

    return {
        "portal_access": {
            "school_admin": (
                unrestricted
                or has_role(
                    user=user,
                    school=school,
                    role_code="school-admin",
                )
            ),

            "academic": (
                allowed(
                    "assessments.approve_subject_result"
                )
                or allowed(
                    "reports.view_termresult"
                )
            ),

            "teacher": has_role(
                user=user,
                school=school,
                role_code="teacher",
            ),

            "finance": allowed(
                "finance.view_studentinvoice"
            ),

            "parent": has_role(
                user=user,
                school=school,
                role_code="parent",
            ),

            "student": has_role(
                user=user,
                school=school,
                role_code="student",
            ),

            "students": allowed(
                "students.view_student"
            ),

            "students_add": allowed(
                "students.add_student"
            ),

            "guardians": allowed(
                "guardians.view_guardian"
            ),

            "guardians_add": allowed(
                "guardians.add_guardian"
            ),

            "staff": allowed(
                "staff.view_staff"
            ),

            "staff_add": allowed(
                "staff.add_staff"
            ),

            "users": allowed(
                "schools.manage_school_users"
            ),

            "settings": allowed(
                "schools.manage_school_settings"
            ),

            "promotions": allowed(
                "promotions.view_promotionevaluation"
            ),
        },
    }


def portal_theme(
    request,
):
    school = getattr(
        request,
        "school",
        None,
    )

    branding = None

    if school:

        try:
            branding = school.branding

        except (
            AttributeError,
            ObjectDoesNotExist,
        ):
            branding = None

    school_name = (
        school.name
        if school
        else "School Portal"
    )

    currency_code = (
        getattr(
            school,
            "currency",
            "",
        )
        or "GHS"
    )

    return {
        "portal_theme": {
            "school_name": school_name,

            "motto": (
                branding.motto
                if branding
                and branding.motto
                else "School Management Portal"
            ),

            "logo_url": (
                branding.logo_url
                if branding
                else ""
            ),

            "primary_color": safe_color(
                (
                    branding.primary_color
                    if branding
                    else None
                ),
                "#7C3AED",
            ),

            "secondary_color": safe_color(
                (
                    branding.secondary_color
                    if branding
                    else None
                ),
                "#FFFFFF",
            ),

            "accent_color": safe_color(
                (
                    branding.accent_color
                    if branding
                    else None
                ),
                "#8B5CF6",
            ),

            "currency_code": currency_code,
        },
    }