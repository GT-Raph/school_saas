from datetime import date

from django.test import TestCase

from apps.academics.models import (
    AcademicYear,
    ClassLevel,
    ClassSection,
    Enrollment,
)
from apps.promotions.models import (
    PromotionEvaluation,
    PromotionPolicy,
)
from apps.promotions.services import (
    evaluate_student_promotion,
)
from apps.schools.models import School
from apps.students.models import Student


class PromotionEngineTests(
    TestCase
):

    def setUp(self):

        self.school = (
            School.objects.create(
                name="Promotion Academy",
                slug="promotion-academy",
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
            )
        )

        self.basic4 = (
            ClassLevel.objects.create(
                school=self.school,
                name="Basic 4",
                code="basic-4",
                order=4,
            )
        )

        self.basic5 = (
            ClassLevel.objects.create(
                school=self.school,
                name="Basic 5",
                code="basic-5",
                order=5,
            )
        )

        self.basic4.next_level = (
            self.basic5
        )

        self.basic4.full_clean()
        self.basic4.save()

        self.section = (
            ClassSection.objects.create(
                school=self.school,
                level=self.basic4,
                name="A",
                code="a",
            )
        )

        self.student = (
            Student.objects.create(
                school=self.school,
                admission_number="PA-001",
                first_name="Ama",
                last_name="Mensah",
            )
        )

        self.enrollment = Enrollment(
            school=self.school,
            student=self.student,
            academic_year=self.year,
            class_section=self.section,
            enrolled_on=date(
                2026,
                9,
                1,
            ),
        )

        self.enrollment.full_clean()
        self.enrollment.save()

        self.policy = (
            PromotionPolicy.objects.create(
                school=self.school,
                name="Basic 4 Policy",
                academic_year=self.year,
                class_level=self.basic4,
                minimum_overall_average=50,
                subject_pass_mark=50,
                maximum_failed_subjects=2,
                minimum_attendance_percentage=75,
                require_all_terms=True,
            )
        )

    def test_missing_term_results_requires_review(
        self,
    ):

        evaluation = (
            evaluate_student_promotion(
                policy=self.policy,
                enrollment=self.enrollment,
            )
        )

        self.assertEqual(
            evaluation.recommendation,
            (
                PromotionEvaluation
                .Recommendation.REVIEW
            ),
        )

        self.assertTrue(
            len(
                evaluation.reasons
            )
            > 0
        )