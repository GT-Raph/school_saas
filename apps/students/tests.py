from datetime import date

from django.core.exceptions import (
    ValidationError,
)
from django.test import TestCase

from apps.accounts.models import User
from apps.academics.models import (
    AcademicYear,
    ClassLevel,
    ClassSection,
)
from apps.schools.models import School
from apps.students.models import Student
from apps.students.services import (
    admit_student,
)
from apps.subscriptions.models import (
    SchoolSubscription,
    SubscriptionPlan,
)


class StudentAdmissionTests(
    TestCase
):

    def setUp(self):

        self.school = (
            School.objects.create(
                name="Admission Academy",
                slug="admission-academy",
            )
        )

        self.user = (
            User.objects.create_user(
                username="admissionadmin",
                password="Password123!",
            )
        )

        plan = (
            SubscriptionPlan.objects.create(
                name="One Student Plan",
                code="one-student",
                active_student_limit=1,
                admin_user_limit=5,
            )
        )

        SchoolSubscription.objects.create(
            school=self.school,

            plan=plan,

            status=(
                SchoolSubscription
                .Status.ACTIVE
            ),

            period_start=date(
                2026,
                9,
                1,
            ),

            period_end=date(
                2027,
                8,
                31,
            ),
        )

        self.year = (
            AcademicYear.objects.create(
                school=self.school,

                name="2026/2027",

                starts_on=date(
                    2026,
                    9,
                    1,
                ),

                ends_on=date(
                    2027,
                    7,
                    31,
                ),

                is_current=True,

                status=(
                    AcademicYear
                    .Status.ACTIVE
                ),
            )
        )

        level = (
            ClassLevel.objects.create(
                school=self.school,

                name="Basic 1",

                code="basic-1",

                order=1,
            )
        )

        self.section = (
            ClassSection.objects.create(
                school=self.school,

                level=level,

                name="A",

                code="a",
            )
        )

    def admission_data(
        self,
        number,
    ):

        return {
            "admission_number":
                number,

            "first_name":
                "Ama",

            "middle_name":
                "",

            "last_name":
                "Mensah",

            "date_of_birth":
                None,

            "gender":
                Student.Gender.FEMALE,

            "admission_date":
                date(
                    2026,
                    9,
                    1,
                ),

            "phone_number":
                "",

            "email":
                "",

            "academic_year":
                self.year,

            "class_section":
                self.section,

            "enrolled_on":
                date(
                    2026,
                    9,
                    1,
                ),
        }

    def test_plan_limit_prevents_second_admission(
        self,
    ):

        admit_student(
            school=self.school,

            data=self.admission_data(
                "AA-001"
            ),

            created_by=self.user,
        )

        with self.assertRaises(
            ValidationError
        ):

            admit_student(
                school=self.school,

                data=self.admission_data(
                    "AA-002"
                ),

                created_by=self.user,
            )

        self.assertEqual(
            Student.objects
            .for_school(
                self.school
            )
            .count(),
            1,
        )