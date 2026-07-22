from datetime import date
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase

from apps.academics.models import (
    AcademicYear,
    ClassLevel,
    ClassSection,
    Enrollment,
    Subject,
    SubjectOffering,
    Term,
)

from apps.assessments.models import (
    Assessment,
    AssessmentCategory,
    AssessmentScheme,
    GradeBand,
    GradeScale,
    OfferingAssessmentPlan,
)

from apps.assessments.services import (
    calculate_subject_result,
    save_student_score,
    validate_scheme_weights,
)

from apps.schools.models import School
from apps.students.models import Student


class AssessmentEngineTests(TestCase):

    def setUp(self):

        self.school = School.objects.create(
            name="Test Academy",
            slug="test-academy",
        )

        self.year = AcademicYear.objects.create(
            school=self.school,
            name="2026/2027",
            starts_on=date(2026, 9, 1),
            ends_on=date(2027, 7, 31),
        )

        self.term = Term(
            school=self.school,
            academic_year=self.year,
            name="Term 1",
            sequence=1,
            starts_on=date(2026, 9, 1),
            ends_on=date(2026, 12, 20),
        )

        self.term.full_clean()
        self.term.save()

        self.level = ClassLevel.objects.create(
            school=self.school,
            name="Basic 4",
            code="basic-4",
            order=4,
        )

        self.section = ClassSection(
            school=self.school,
            level=self.level,
            name="A",
            code="a",
        )

        self.section.full_clean()
        self.section.save()

        self.subject = Subject.objects.create(
            school=self.school,
            name="Mathematics",
            code="mathematics",
        )

        self.offering = SubjectOffering(
            school=self.school,
            academic_year=self.year,
            class_section=self.section,
            subject=self.subject,
        )

        self.offering.full_clean()
        self.offering.save()

        self.student = Student.objects.create(
            school=self.school,
            admission_number="TA-001",
            first_name="Ama",
            last_name="Mensah",
        )

        self.enrollment = Enrollment(
            school=self.school,
            student=self.student,
            academic_year=self.year,
            class_section=self.section,
            enrolled_on=date(2026, 9, 1),
        )

        self.enrollment.full_clean()
        self.enrollment.save()

        self.scheme = AssessmentScheme.objects.create(
            school=self.school,
            name="40/60 Scheme",
            code="40-60",
            academic_year=self.year,
        )

        self.ca_category = (
            AssessmentCategory.objects.create(
                school=self.school,
                scheme=self.scheme,
                name="CA",
                code="ca",
                weight=40,
                sequence=1,
            )
        )

        self.exam_category = (
            AssessmentCategory.objects.create(
                school=self.school,
                scheme=self.scheme,
                name="Exam",
                code="exam",
                weight=60,
                sequence=2,
            )
        )

        self.grade_scale = (
            GradeScale.objects.create(
                school=self.school,
                name="Standard",
                code="standard",
            )
        )

        for grade, low, high in [
            ("A", Decimal("80.00"), Decimal("100.00")),
            ("B", Decimal("70.00"), Decimal("79.99")),
            ("C", Decimal("60.00"), Decimal("69.99")),
            ("D", Decimal("50.00"), Decimal("59.99")),
            ("F", Decimal("0.00"), Decimal("49.99")),
        ]:
            print(
                "CREATING BAND:",
                grade,
                repr(low),
                repr(high),
                type(high),
            )

            band = GradeBand(
                school=self.school,
                grade_scale=self.grade_scale,
                grade=grade,
                minimum_score=low,
                maximum_score=high,
            )

            band.full_clean()
            band.save()

        self.plan = OfferingAssessmentPlan(
            school=self.school,
            offering=self.offering,
            term=self.term,
            scheme=self.scheme,
            grade_scale=self.grade_scale,
        )

        self.plan.full_clean()
        self.plan.save()

    def test_scheme_weights_equal_100(self):

        self.assertTrue(
            validate_scheme_weights(
                self.scheme
            )
        )

    def test_score_cannot_exceed_maximum(self):

        assessment = Assessment.objects.create(
            school=self.school,
            assessment_plan=self.plan,
            category=self.ca_category,
            name="Class Test",
            max_score=20,
            status=Assessment.Status.OPEN,
        )

        with self.assertRaises(
            ValidationError
        ):
            save_student_score(
                school=self.school,
                assessment=assessment,
                enrollment=self.enrollment,
                raw_score=25,
            )

    def test_weighted_result_calculation(self):

        ca = Assessment.objects.create(
            school=self.school,
            assessment_plan=self.plan,
            category=self.ca_category,
            name="CA Total",
            max_score=40,
            status=Assessment.Status.CLOSED,
        )

        exam = Assessment.objects.create(
            school=self.school,
            assessment_plan=self.plan,
            category=self.exam_category,
            name="Final Exam",
            max_score=100,
            status=Assessment.Status.CLOSED,
        )

        save_student_score(
            school=self.school,
            assessment=ca,
            enrollment=self.enrollment,
            raw_score=34,
        )

        save_student_score(
            school=self.school,
            assessment=exam,
            enrollment=self.enrollment,
            raw_score=78,
        )

        result = calculate_subject_result(
            assessment_plan=self.plan,
            enrollment=self.enrollment,
        )

        self.assertEqual(
            result.total_score,
            Decimal("80.80"),
        )

        self.assertEqual(
            result.grade,
            "A",
        )