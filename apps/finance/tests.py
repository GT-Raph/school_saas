from datetime import date
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone

from apps.accounts.models import User

from apps.academics.models import (
    AcademicYear,
    ClassLevel,
    ClassSection,
    Enrollment,
    Term,
)

from apps.finance.models import (
    FeeCategory,
    FeeStructure,
    FeeStructureItem,
    FinancialAdjustment,
    Payment,
)

from apps.finance.services import (
    apply_financial_adjustment,
    generate_invoice_from_fee_structure,
    get_invoice_balance,
    issue_invoice,
    record_payment,
    reverse_payment,
)

from apps.schools.models import School
from apps.students.models import Student


class FinanceEngineTests(
    TestCase
):

    def setUp(self):

        self.user = (
            User.objects.create_user(
                username="financeadmin",
                password="test-password",
            )
        )

        self.school = (
            School.objects.create(
                name="Finance Academy",
                slug="finance-academy",
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

        self.term = Term(
            school=self.school,
            academic_year=self.year,
            name="Term 1",
            sequence=1,

            starts_on=date(
                2026,
                9,
                1,
            ),

            ends_on=date(
                2026,
                12,
                20,
            ),
        )

        self.term.full_clean()
        self.term.save()

        self.level = (
            ClassLevel.objects.create(
                school=self.school,
                name="Basic 4",
                code="basic-4",
                order=4,
            )
        )

        self.section = ClassSection(
            school=self.school,
            level=self.level,
            name="A",
            code="a",
        )

        self.section.full_clean()
        self.section.save()

        self.student = (
            Student.objects.create(
                school=self.school,

                admission_number=(
                    "FIN-001"
                ),

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

        self.tuition = (
            FeeCategory.objects.create(
                school=self.school,
                name="Tuition",
                code="tuition",
            )
        )

        self.structure = FeeStructure(
            school=self.school,

            name=(
                "Basic 4 Term 1"
            ),

            code=(
                "basic4-term1"
            ),

            academic_year=self.year,
            term=self.term,
            class_level=self.level,

            status=(
                FeeStructure
                .Status.ACTIVE
            ),
        )

        self.structure.full_clean()
        self.structure.save()

        item = FeeStructureItem(
            school=self.school,

            fee_structure=(
                self.structure
            ),

            category=self.tuition,

            description="Tuition",

            amount=Decimal(
                "5000.00"
            ),
        )

        item.full_clean()
        item.save()

        self.invoice = (
            generate_invoice_from_fee_structure(
                school=self.school,

                enrollment=(
                    self.enrollment
                ),

                fee_structure=(
                    self.structure
                ),

                issue_date=date(
                    2026,
                    9,
                    1,
                ),

                issued_by=self.user,
            )
        )

        issue_invoice(
            invoice=self.invoice,
            user=self.user,
        )

    def test_invoice_creates_debit_balance(
        self,
    ):
        self.assertEqual(
            get_invoice_balance(
                self.invoice
            ),
            Decimal(
                "5000.00"
            ),
        )

    def test_payment_reduces_balance(
        self,
    ):

        record_payment(
            school=self.school,

            enrollment=(
                self.enrollment
            ),

            amount=Decimal(
                "2000.00"
            ),

            method=(
                Payment.Method.CASH
            ),

            paid_at=timezone.now(),

            allocations=[
                {
                    "invoice":
                        self.invoice,

                    "amount":
                        Decimal(
                            "2000.00"
                        ),
                }
            ],

            recorded_by=(
                self.user
            ),
        )

        self.assertEqual(
            get_invoice_balance(
                self.invoice
            ),
            Decimal(
                "3000.00"
            ),
        )

    def test_scholarship_reduces_balance(
        self,
    ):

        apply_financial_adjustment(
            invoice=self.invoice,

            adjustment_type=(
                FinancialAdjustment
                .Type.SCHOLARSHIP
            ),

            amount=Decimal(
                "500.00"
            ),

            reason=(
                "Merit scholarship"
            ),

            approved_by=(
                self.user
            ),
        )

        self.assertEqual(
            get_invoice_balance(
                self.invoice
            ),
            Decimal(
                "4500.00"
            ),
        )

    def test_payment_reversal_restores_balance(
        self,
    ):

        payment = record_payment(
            school=self.school,

            enrollment=(
                self.enrollment
            ),

            amount=Decimal(
                "2000.00"
            ),

            method=(
                Payment.Method.CASH
            ),

            paid_at=timezone.now(),

            allocations=[
                {
                    "invoice":
                        self.invoice,

                    "amount":
                        Decimal(
                            "2000.00"
                        ),
                }
            ],

            recorded_by=(
                self.user
            ),
        )

        self.assertEqual(
            get_invoice_balance(
                self.invoice
            ),
            Decimal(
                "3000.00"
            ),
        )

        reverse_payment(
            payment=payment,

            reason=(
                "Incorrect payment"
            ),

            reversed_by=(
                self.user
            ),
        )

        self.assertEqual(
            get_invoice_balance(
                self.invoice
            ),
            Decimal(
                "5000.00"
            ),
        )

    def test_overpayment_is_blocked(
        self,
    ):

        with self.assertRaises(
            Exception
        ):
            record_payment(
                school=self.school,

                enrollment=(
                    self.enrollment
                ),

                amount=Decimal(
                    "6000.00"
                ),

                method=(
                    Payment.Method.CASH
                ),

                paid_at=(
                    timezone.now()
                ),

                allocations=[
                    {
                        "invoice":
                            self.invoice,

                        "amount":
                            Decimal(
                                "6000.00"
                            ),
                    }
                ],

                recorded_by=(
                    self.user
                ),
            )