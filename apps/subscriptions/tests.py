from datetime import date

from django.core.exceptions import (
    ValidationError,
)
from django.test import TestCase

from apps.academics.models import (
    AcademicYear,
    ClassLevel,
    ClassSection,
    Enrollment,
)
from apps.schools.models import School
from apps.students.models import Student
from apps.subscriptions.models import (
    SchoolSubscription,
    SubscriptionPlan,
)
from apps.subscriptions.services import (
    assert_can_add_active_students,
    get_active_student_count,
)


class SubscriptionUsageTests(
    TestCase
):

    def setUp(self):

        self.school = (
            School.objects.create(
                name="Limit Academy",
                slug="limit-academy",
            )
        )

        self.plan = (
            SubscriptionPlan.objects.create(
                name="Test Plan",
                code="test-plan",
                active_student_limit=2,
                admin_user_limit=5,
            )
        )

        self.subscription = (
            SchoolSubscription.objects.create(
                school=self.school,

                plan=self.plan,

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

        self.level = (
            ClassLevel.objects.create(
                school=self.school,

                name="Basic 4",

                code="basic-4",

                order=4,
            )
        )

        self.section = (
            ClassSection.objects.create(
                school=self.school,

                level=self.level,

                name="A",

                code="a",
            )
        )

    def create_active_student(
        self,
        number,
    ):

        student = (
            Student.objects.create(
                school=self.school,

                admission_number=number,

                first_name="Student",

                last_name=number,

                status=(
                    Student.Status.ACTIVE
                ),
            )
        )

        enrollment = Enrollment(
            school=self.school,

            student=student,

            academic_year=self.year,

            class_section=self.section,

            status=(
                Enrollment.Status.ACTIVE
            ),

            enrolled_on=date(
                2026,
                9,
                1,
            ),
        )

        enrollment.full_clean()
        enrollment.save()

        return student

    def test_active_student_count(
        self,
    ):

        self.create_active_student(
            "A-001"
        )

        self.assertEqual(
            get_active_student_count(
                school=self.school
            ),
            1,
        )

    def test_plan_limit_blocks_overage(
        self,
    ):

        self.create_active_student(
            "A-001"
        )

        self.create_active_student(
            "A-002"
        )

        with self.assertRaises(
            ValidationError
        ):

            assert_can_add_active_students(
                school=self.school,

                additional_count=1,
            )