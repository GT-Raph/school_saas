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


class TenantIsolationModelTests(
    TestCase
):
    def test_student_cannot_have_two_enrollments_same_year(
        self,
    ):
        student = Student.objects.create(
            school=self.school_a,
            admission_number="A-002",
            first_name="Yaw",
            last_name="Asare",
        )

        Enrollment.objects.create(
            school=self.school_a,
            student=student,
            academic_year=self.year_a,
            class_section=self.section_a,
            enrolled_on=date(
                2026,
                9,
                1,
            ),
        )

        duplicate = Enrollment(
            school=self.school_a,
            student=student,
            academic_year=self.year_a,
            class_section=self.section_a,
            enrolled_on=date(
                2026,
                9,
                2,
            ),
        )

        with self.assertRaises(
            ValidationError
        ):
            duplicate.full_clean()

    def setUp(self):
        self.school_a = (
            School.objects.create(
                name="School A",
                slug="school-a",
            )
        )

        self.school_b = (
            School.objects.create(
                name="School B",
                slug="school-b",
            )
        )

        self.year_a = (
            AcademicYear.objects.create(
                school=self.school_a,
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
            )
        )

        self.level_a = (
            ClassLevel.objects.create(
                school=self.school_a,
                name="Basic 4",
                code="basic-4",
                order=4,
            )
        )

        self.section_a = (
            ClassSection.objects.create(
                school=self.school_a,
                level=self.level_a,
                name="A",
                code="a",
            )
        )

        self.student_b = (
            Student.objects.create(
                school=self.school_b,
                admission_number="B-001",
                first_name="Kwame",
                last_name="Mensah",
            )
        )

    def test_cross_school_enrollment_fails(
        self,
    ):
        enrollment = Enrollment(
            school=self.school_a,
            student=self.student_b,
            academic_year=self.year_a,
            class_section=self.section_a,
            enrolled_on=date(
                2026,
                9,
                1,
            ),
        )

        with self.assertRaises(
            ValidationError
        ):
            enrollment.full_clean()

    def test_for_school_manager_scopes_data(
        self,
    ):
        Student.objects.create(
            school=self.school_a,
            admission_number="A-001",
            first_name="Ama",
            last_name="Owusu",
        )

        school_a_students = (
            Student.objects.for_school(
                self.school_a
            )
        )

        self.assertEqual(
            school_a_students.count(),
            1,
        )

        self.assertEqual(
            school_a_students.first()
            .school_id,
            self.school_a.id,
        )