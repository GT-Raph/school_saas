from django.contrib.auth.models import Permission
from django.core.exceptions import ValidationError
from django.db import transaction

from apps.accounts.models import User
from config import settings

from .models import (
    School,
    SchoolDomain,
    SchoolMembership,
    SchoolRole,
)


ROLE_NAMES = {
    "school-admin": "School Administrator",
    "academic-admin": "Academic Administrator",
    "teacher": "Teacher",
    "finance": "Finance Officer",
    "parent": "Parent / Guardian",
    "student": "Student",
}


ROLE_PERMISSIONS = {
    "school-admin": [
        "schools.manage_school_settings",
        "schools.manage_school_users",
        "schools.manage_school_roles",

        "students.view_student",
        "students.add_student",
        "students.change_student",

        "guardians.view_guardian",
        "guardians.add_guardian",
        "guardians.change_guardian",

        "guardians.view_studentguardian",
        "guardians.add_studentguardian",
        "guardians.change_studentguardian",

        "staff.view_staff",
        "staff.add_staff",
        "staff.change_staff",

        "academics.view_academicyear",
        "academics.view_term",
        "academics.view_classlevel",
        "academics.view_classsection",
        "academics.view_subject",
        "academics.view_enrollment",

        "reports.view_termresult",
        "reports.view_reportcard",
    ],

    "academic-admin": [
        "students.view_student",

        "academics.view_academicyear",
        "academics.view_term",
        "academics.view_classlevel",
        "academics.view_classsection",
        "academics.view_subject",
        "academics.view_enrollment",

        "assessments.view_score",
        "assessments.view_subjectresult",
        "assessments.approve_subject_result",
        "assessments.publish_subject_result",

        "reports.view_termresult",
        "reports.change_termresult",
        "reports.view_reportcard",
        "reports.change_reportcard",

        "promotions.view_promotionevaluation",
        "promotions.run_promotion_evaluation",
        "promotions.approve_promotion_decision",
        "promotions.execute_promotion_decision",
    ],

    "teacher": [
        "students.view_student",

        "academics.view_enrollment",
        "academics.view_subjectoffering",
        "academics.view_teacherassignment",

        "attendance.view_attendancesession",
        "attendance.add_attendancesession",
        "attendance.change_attendancesession",

        "attendance.view_attendancerecord",
        "attendance.add_attendancerecord",
        "attendance.change_attendancerecord",

        "attendance.submit_attendance",

        "assessments.view_assessment",
        "assessments.view_score",
        "assessments.add_score",
        "assessments.change_score",
        "assessments.view_subjectresult",
        "assessments.submit_subject_result",
    ],

    "finance": [
        "students.view_student",

        "guardians.view_guardian",

        "academics.view_enrollment",

        "finance.view_feecategory",
        "finance.view_feestructure",
        "finance.view_studentinvoice",
        "finance.view_payment",
        "finance.view_receipt",
        "finance.view_ledgerentry",

        "finance.record_student_payment",
        "finance.issue_student_invoice",
    ],

    "parent": [],

    "student": [],
}

@transaction.atomic
def ensure_default_school_roles(
    *,
    school,
):
    for role_code, role_name in ROLE_NAMES.items():

        role, _ = SchoolRole.objects.get_or_create(
            school=school,
            code=role_code,
            defaults={
                "name": role_name,
                "is_system_role": True,
            },
        )

        permission_objects = []

        for full_permission in ROLE_PERMISSIONS.get(
            role_code,
            [],
        ):

            app_label, codename = (
                full_permission.split(
                    ".",
                    1,
                )
            )

            permission = (
                Permission.objects.filter(
                    content_type__app_label=app_label,
                    codename=codename,
                )
                .first()
            )

            if permission:
                permission_objects.append(
                    permission
                )

        role.permissions.set(
            permission_objects
        )

    return school

@transaction.atomic
def create_school_administrator(
    *,
    school,
    username,
    password,
    first_name="",
    last_name="",
    email="",
):
    ensure_default_school_roles(
        school=school
    )

    if User.objects.filter(
        username=username
    ).exists():
        raise ValidationError(
            "This username already exists."
        )

    user = User.objects.create_user(
        username=username,
        password=password,
        first_name=first_name,
        last_name=last_name,
        email=email,
        must_change_password=True,
    )

    membership = (
        SchoolMembership.objects.create(
            school=school,
            user=user,
            is_active=True,
        )
    )

    admin_role = (
        SchoolRole.objects.get(
            school=school,
            code="school-admin",
        )
    )

    membership.roles.add(
        admin_role
    )

    return membership

def ensure_development_domain(
    *,
    school,
):
    if not settings.DEBUG:
        return None

    return SchoolDomain.objects.update_or_create(
        domain=f"{school.slug}.localhost",
        defaults={
            "school": school,
            "is_verified": True,
            "is_primary": False,
        },
    )[0]