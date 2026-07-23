from django.contrib.auth.models import (
    Permission,
)
from django.core.management.base import (
    BaseCommand,
    CommandError,
)

from apps.schools.models import (
    School,
    SchoolRole,
)


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


ROLE_NAMES = {

    "school-admin":
        "School Administrator",

    "academic-admin":
        "Academic Administrator",

    "teacher":
        "Teacher",

    "finance":
        "Finance Officer",

    "parent":
        "Parent / Guardian",

    "student":
        "Student",
}


class Command(BaseCommand):

    help = (
        "Create or synchronize "
        "default roles for a school."
    )

    def add_arguments(
        self,
        parser,
    ):
        parser.add_argument(
            "--school",
            required=True,
            help="School slug",
        )

    def handle(
        self,
        *args,
        **options,
    ):
        slug = options["school"]

        try:
            school = School.objects.get(
                slug=slug
            )

        except School.DoesNotExist:

            raise CommandError(
                f"School '{slug}' "
                f"does not exist."
            )

        for (
            role_code,
            permission_names,
        ) in ROLE_PERMISSIONS.items():

            role, _ = (
                SchoolRole.objects
                .get_or_create(
                    school=school,
                    code=role_code,
                    defaults={
                        "name": (
                            ROLE_NAMES[
                                role_code
                            ]
                        ),
                        "is_system_role":
                            True,
                    },
                )
            )

            permissions = []

            for full_name in (
                permission_names
            ):
                app_label, codename = (
                    full_name.split(
                        ".",
                        1,
                    )
                )

                try:
                    permission = (
                        Permission.objects
                        .get(
                            content_type__app_label=(
                                app_label
                            ),
                            codename=(
                                codename
                            ),
                        )
                    )

                except (
                    Permission.DoesNotExist
                ):
                    self.stdout.write(
                        self.style.WARNING(
                            (
                                "Permission "
                                f"not found: "
                                f"{full_name}"
                            )
                        )
                    )

                    continue

                permissions.append(
                    permission
                )

            role.permissions.set(
                permissions
            )

            self.stdout.write(
                self.style.SUCCESS(
                    (
                        f"Configured role: "
                        f"{role.name}"
                    )
                )
            )

        self.stdout.write(
            self.style.SUCCESS(
                (
                    "School roles "
                    "configured successfully."
                )
            )
        )