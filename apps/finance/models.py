from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from apps.core.models import SchoolOwnedModel


class FeeCategory(SchoolOwnedModel):
    """
    Examples:

    Tuition
    Books
    ICT
    Transport
    Feeding
    Examination Fee
    PTA Levy
    """

    name = models.CharField(
        max_length=150,
    )

    code = models.SlugField(
        max_length=80,
    )

    description = models.TextField(
        blank=True,
    )

    is_active = models.BooleanField(
        default=True,
    )

    class Meta:
        ordering = [
            "name",
        ]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "school",
                    "code",
                ],
                name=(
                    "unique_fee_category_"
                    "code_per_school"
                ),
            ),
        ]

    def __str__(self):
        return self.name


class FeeStructure(SchoolOwnedModel):
    """
    Defines what a class should pay for a term.

    Example:

    2026/2027
    Term 1
    Basic 4

    Tuition    GHS 3,000
    ICT        GHS   300
    Books      GHS   500
    """

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        ACTIVE = "active", "Active"
        ARCHIVED = "archived", "Archived"

    name = models.CharField(
        max_length=180,
    )

    code = models.SlugField(
        max_length=100,
    )

    academic_year = models.ForeignKey(
        "academics.AcademicYear",
        on_delete=models.PROTECT,
        related_name="fee_structures",
    )

    term = models.ForeignKey(
        "academics.Term",
        on_delete=models.PROTECT,
        related_name="fee_structures",
    )

    class_level = models.ForeignKey(
        "academics.ClassLevel",
        on_delete=models.PROTECT,
        related_name="fee_structures",
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
    )

    notes = models.TextField(
        blank=True,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "school",
                    "academic_year",
                    "term",
                    "class_level",
                    "code",
                ],
                name=(
                    "unique_fee_structure_"
                    "per_context"
                ),
            ),
        ]

    def clean(self):
        errors = {}

        for field_name, obj in [
            (
                "academic_year",
                self.academic_year
                if self.academic_year_id
                else None,
            ),
            (
                "term",
                self.term
                if self.term_id
                else None,
            ),
            (
                "class_level",
                self.class_level
                if self.class_level_id
                else None,
            ),
        ]:
            if (
                obj
                and self.school_id
                and obj.school_id
                != self.school_id
            ):
                errors[field_name] = (
                    f"{field_name.replace('_', ' ').title()} "
                    "belongs to another school."
                )

        if (
            self.term_id
            and self.academic_year_id
            and self.term.academic_year_id
            != self.academic_year_id
        ):
            errors["term"] = (
                "Term does not belong to "
                "the selected academic year."
            )

        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return (
            f"{self.name} - "
            f"{self.term}"
        )


class FeeStructureItem(SchoolOwnedModel):

    fee_structure = models.ForeignKey(
        FeeStructure,
        on_delete=models.CASCADE,
        related_name="items",
    )

    category = models.ForeignKey(
        FeeCategory,
        on_delete=models.PROTECT,
        related_name="fee_structure_items",
    )

    description = models.CharField(
        max_length=255,
        blank=True,
    )

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )

    is_mandatory = models.BooleanField(
        default=True,
    )

    sequence = models.PositiveSmallIntegerField(
        default=1,
    )

    class Meta:
        ordering = [
            "sequence",
        ]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "fee_structure",
                    "category",
                ],
                name=(
                    "unique_fee_category_"
                    "per_structure"
                ),
            ),

            models.CheckConstraint(
                condition=models.Q(
                    amount__gte=0
                ),
                name=(
                    "fee_structure_item_"
                    "amount_not_negative"
                ),
            ),
        ]

    def clean(self):
        errors = {}

        if (
            self.fee_structure_id
            and self.school_id
            and self.fee_structure.school_id
            != self.school_id
        ):
            errors["fee_structure"] = (
                "Fee structure belongs "
                "to another school."
            )

        if (
            self.category_id
            and self.school_id
            and self.category.school_id
            != self.school_id
        ):
            errors["category"] = (
                "Fee category belongs "
                "to another school."
            )

        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return (
            f"{self.category.name}: "
            f"{self.amount}"
        )


class StudentInvoice(SchoolOwnedModel):

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        ISSUED = "issued", "Issued"
        PARTIALLY_PAID = (
            "partially_paid",
            "Partially Paid",
        )
        PAID = "paid", "Paid"
        VOID = "void", "Void"

    invoice_number = models.CharField(
        max_length=100,
    )

    billing_key = models.CharField(
        max_length=255,
        blank=True,
        default="",
    )

    enrollment = models.ForeignKey(
        "academics.Enrollment",
        on_delete=models.PROTECT,
        related_name="invoices",
    )

    term = models.ForeignKey(
        "academics.Term",
        on_delete=models.PROTECT,
        related_name="student_invoices",
    )

    fee_structure = models.ForeignKey(
        FeeStructure,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="invoices",
    )

    issue_date = models.DateField()

    due_date = models.DateField(
        null=True,
        blank=True,
    )

    gross_total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
    )

    status = models.CharField(
        max_length=30,
        choices=Status.choices,
        default=Status.DRAFT,
    )

    notes = models.TextField(
        blank=True,
    )

    issued_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="invoices_issued",
    )

    issued_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    class Meta:
        ordering = [
            "-issue_date",
            "-created_at",
        ]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "school",
                    "invoice_number",
                ],
                name=(
                    "unique_invoice_number_"
                    "per_school"
                ),
            ),

            models.UniqueConstraint(
                fields=[
                    "school",
                    "billing_key",
                ],
                condition=~models.Q(
                    billing_key=""
                ),
                name=(
                    "unique_invoice_billing_key_"
                    "per_school"
                ),
            ),

            models.CheckConstraint(
                condition=models.Q(
                    gross_total__gte=0
                ),
                name=(
                    "invoice_gross_total_"
                    "not_negative"
                ),
            ),
        ]

        permissions = [
            (
                "issue_student_invoice",
                "Can issue student invoices",
            ),
            (
                "void_student_invoice",
                "Can void student invoices",
            ),
        ]

        indexes = [
            models.Index(
                fields=[
                    "school",
                    "status",
                ]
            ),
            models.Index(
                fields=[
                    "school",
                    "enrollment",
                ]
            ),
        ]

    def clean(self):
        errors = {}

        if (
            self.enrollment_id
            and self.school_id
            and self.enrollment.school_id
            != self.school_id
        ):
            errors["enrollment"] = (
                "Enrollment belongs "
                "to another school."
            )

        if (
            self.term_id
            and self.school_id
            and self.term.school_id
            != self.school_id
        ):
            errors["term"] = (
                "Term belongs "
                "to another school."
            )

        if (
            self.enrollment_id
            and self.term_id
            and self.enrollment.academic_year_id
            != self.term.academic_year_id
        ):
            errors["term"] = (
                "Invoice term does not match "
                "the enrollment academic year."
            )

        if (
            self.fee_structure_id
            and self.school_id
            and self.fee_structure.school_id
            != self.school_id
        ):
            errors["fee_structure"] = (
                "Fee structure belongs "
                "to another school."
            )

        if (
            self.due_date
            and self.issue_date
            and self.due_date
            < self.issue_date
        ):
            errors["due_date"] = (
                "Due date cannot be "
                "before issue date."
            )

        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return self.invoice_number


class InvoiceItem(SchoolOwnedModel):

    invoice = models.ForeignKey(
        StudentInvoice,
        on_delete=models.CASCADE,
        related_name="items",
    )

    fee_category = models.ForeignKey(
        FeeCategory,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="invoice_items",
    )

    description = models.CharField(
        max_length=255,
    )

    quantity = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=1,
    )

    unit_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )

    line_total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(
                    quantity__gt=0
                ),
                name=(
                    "invoice_item_quantity_"
                    "positive"
                ),
            ),

            models.CheckConstraint(
                condition=models.Q(
                    unit_amount__gte=0
                ),
                name=(
                    "invoice_item_unit_amount_"
                    "not_negative"
                ),
            ),

            models.CheckConstraint(
                condition=models.Q(
                    line_total__gte=0
                ),
                name=(
                    "invoice_item_line_total_"
                    "not_negative"
                ),
            ),
        ]

    def clean(self):
        if (
            self.invoice_id
            and self.school_id
            and self.invoice.school_id
            != self.school_id
        ):
            raise ValidationError(
                {
                    "invoice": (
                        "Invoice belongs "
                        "to another school."
                    )
                }
            )

        expected = (
            self.quantity
            * self.unit_amount
        )

        if (
            self.line_total
            != expected
        ):
            raise ValidationError(
                {
                    "line_total": (
                        "Line total must equal "
                        "quantity × unit amount."
                    )
                }
            )

    def __str__(self):
        return self.description


class Payment(SchoolOwnedModel):

    class Method(models.TextChoices):
        CASH = "cash", "Cash"
        MOBILE_MONEY = (
            "mobile_money",
            "Mobile Money",
        )
        BANK_TRANSFER = (
            "bank_transfer",
            "Bank Transfer",
        )
        CHEQUE = "cheque", "Cheque"
        CARD = "card", "Card"
        ONLINE = "online", "Online"
        OTHER = "other", "Other"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        CONFIRMED = (
            "confirmed",
            "Confirmed",
        )
        REVERSED = (
            "reversed",
            "Reversed",
        )

    payment_number = models.CharField(
        max_length=100,
    )

    enrollment = models.ForeignKey(
        "academics.Enrollment",
        on_delete=models.PROTECT,
        related_name="payments",
    )

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )

    method = models.CharField(
        max_length=30,
        choices=Method.choices,
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )

    paid_at = models.DateTimeField()

    payer_name = models.CharField(
        max_length=180,
        blank=True,
    )

    reference = models.CharField(
        max_length=180,
        blank=True,
    )

    external_reference = models.CharField(
        max_length=255,
        blank=True,
    )

    notes = models.TextField(
        blank=True,
    )

    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="payments_recorded",
    )

    confirmed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="payments_confirmed",
    )

    confirmed_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    class Meta:
        ordering = [
            "-paid_at",
        ]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "school",
                    "payment_number",
                ],
                name=(
                    "unique_payment_number_"
                    "per_school"
                ),
            ),

            models.CheckConstraint(
                condition=models.Q(
                    amount__gt=0
                ),
                name=(
                    "payment_amount_positive"
                ),
            ),
        ]

        permissions = [
            (
                "record_student_payment",
                "Can record student payments",
            ),
            (
                "reverse_student_payment",
                "Can reverse student payments",
            ),
        ]

    def clean(self):
        if (
            self.enrollment_id
            and self.school_id
            and self.enrollment.school_id
            != self.school_id
        ):
            raise ValidationError(
                {
                    "enrollment": (
                        "Enrollment belongs "
                        "to another school."
                    )
                }
            )

    def __str__(self):
        return self.payment_number


class PaymentAllocation(SchoolOwnedModel):
    """
    Allocates one payment to one invoice.

    One payment can settle multiple invoices.
    """

    payment = models.ForeignKey(
        Payment,
        on_delete=models.PROTECT,
        related_name="allocations",
    )

    invoice = models.ForeignKey(
        StudentInvoice,
        on_delete=models.PROTECT,
        related_name="payment_allocations",
    )

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "payment",
                    "invoice",
                ],
                name=(
                    "unique_payment_invoice_"
                    "allocation"
                ),
            ),

            models.CheckConstraint(
                condition=models.Q(
                    amount__gt=0
                ),
                name=(
                    "payment_allocation_"
                    "amount_positive"
                ),
            ),
        ]

    def clean(self):
        errors = {}

        if (
            self.payment_id
            and self.invoice_id
        ):
            if (
                self.payment.school_id
                != self.invoice.school_id
            ):
                errors["invoice"] = (
                    "Payment and invoice belong "
                    "to different schools."
                )

            if (
                self.payment.enrollment_id
                != self.invoice.enrollment_id
            ):
                errors["invoice"] = (
                    "Payment and invoice belong "
                    "to different students/"
                    "enrollments."
                )

        if (
            self.school_id
            and self.payment_id
            and self.payment.school_id
            != self.school_id
        ):
            errors["payment"] = (
                "Payment belongs "
                "to another school."
            )

        if errors:
            raise ValidationError(
                errors
            )

    def __str__(self):
        return (
            f"{self.payment} -> "
            f"{self.invoice}"
        )


class FinancialAdjustment(
    SchoolOwnedModel
):
    """
    Discounts, scholarships, waivers,
    and other approved balance reductions.

    They are NOT implemented by editing the invoice.
    """

    class Type(models.TextChoices):
        DISCOUNT = (
            "discount",
            "Discount",
        )
        SCHOLARSHIP = (
            "scholarship",
            "Scholarship",
        )
        WAIVER = (
            "waiver",
            "Waiver",
        )
        CREDIT = (
            "credit",
            "Other Credit",
        )

    class Status(models.TextChoices):
        APPROVED = (
            "approved",
            "Approved",
        )
        REVERSED = (
            "reversed",
            "Reversed",
        )

    invoice = models.ForeignKey(
        StudentInvoice,
        on_delete=models.PROTECT,
        related_name="adjustments",
    )

    adjustment_type = models.CharField(
        max_length=30,
        choices=Type.choices,
    )

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )

    reason = models.TextField()

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.APPROVED,
    )

    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name=(
            "financial_adjustments_approved"
        ),
    )

    approved_at = models.DateTimeField()

    reversed_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    reversed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name=(
            "financial_adjustments_reversed"
        ),
    )

    reversal_reason = models.TextField(
        blank=True,
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(
                    amount__gt=0
                ),
                name=(
                    "financial_adjustment_"
                    "positive"
                ),
            ),
        ]

        permissions = [
            (
                "approve_financial_adjustment",
                "Can approve discounts, scholarships and waivers",
            ),
            (
                "reverse_financial_adjustment",
                "Can reverse financial adjustments",
            ),
        ]

    def clean(self):
        if (
            self.invoice_id
            and self.school_id
            and self.invoice.school_id
            != self.school_id
        ):
            raise ValidationError(
                {
                    "invoice": (
                        "Invoice belongs "
                        "to another school."
                    )
                }
            )

    def __str__(self):
        return (
            f"{self.adjustment_type} "
            f"{self.amount}"
        )


class PaymentReversal(
    SchoolOwnedModel
):
    """
    Payment correction record.

    Original Payment remains permanently.
    """

    payment = models.OneToOneField(
        Payment,
        on_delete=models.PROTECT,
        related_name="reversal",
    )

    reason = models.TextField()

    reversed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name=(
            "payment_reversals_created"
        ),
    )

    reversed_at = models.DateTimeField()

    def clean(self):
        if (
            self.payment_id
            and self.school_id
            and self.payment.school_id
            != self.school_id
        ):
            raise ValidationError(
                {
                    "payment": (
                        "Payment belongs "
                        "to another school."
                    )
                }
            )

    def __str__(self):
        return (
            f"Reversal: "
            f"{self.payment.payment_number}"
        )


class LedgerEntry(SchoolOwnedModel):
    """
    Student sub-ledger.

    DEBIT increases amount owed.
    CREDIT reduces amount owed.

    Example:

    Invoice              DEBIT   5000
    Payment                       CREDIT 2000
    Discount                      CREDIT 500

    Balance = 2500
    """

    class Type(models.TextChoices):
        INVOICE = (
            "invoice",
            "Invoice Charge",
        )
        PAYMENT = (
            "payment",
            "Payment",
        )
        PAYMENT_REVERSAL = (
            "payment_reversal",
            "Payment Reversal",
        )
        DISCOUNT = (
            "discount",
            "Discount",
        )
        SCHOLARSHIP = (
            "scholarship",
            "Scholarship",
        )
        WAIVER = (
            "waiver",
            "Waiver",
        )
        CREDIT = (
            "credit",
            "Other Credit",
        )
        ADJUSTMENT_REVERSAL = (
            "adjustment_reversal",
            "Adjustment Reversal",
        )

    enrollment = models.ForeignKey(
        "academics.Enrollment",
        on_delete=models.PROTECT,
        related_name="ledger_entries",
    )

    invoice = models.ForeignKey(
        StudentInvoice,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="ledger_entries",
    )

    payment = models.ForeignKey(
        Payment,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="ledger_entries",
    )

    adjustment = models.ForeignKey(
        FinancialAdjustment,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="ledger_entries",
    )

    entry_type = models.CharField(
        max_length=40,
        choices=Type.choices,
    )

    description = models.CharField(
        max_length=255,
    )

    debit = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
    )

    credit = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
    )

    transaction_date = models.DateTimeField()

    reference = models.CharField(
        max_length=180,
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name=(
            "ledger_entries_created"
        ),
    )

    class Meta:
        ordering = [
            "transaction_date",
            "created_at",
        ]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "school",
                    "reference",
                ],
                name=(
                    "unique_ledger_reference_"
                    "per_school"
                ),
            ),

            models.CheckConstraint(
                condition=(
                    models.Q(
                        debit__gte=0
                    )
                    & models.Q(
                        credit__gte=0
                    )
                ),
                name=(
                    "ledger_values_"
                    "not_negative"
                ),
            ),

            models.CheckConstraint(
                condition=(
                    (
                        models.Q(
                            debit__gt=0
                        )
                        & models.Q(
                            credit=0
                        )
                    )
                    |
                    (
                        models.Q(
                            credit__gt=0
                        )
                        & models.Q(
                            debit=0
                        )
                    )
                ),
                name=(
                    "ledger_exactly_one_side"
                ),
            ),
        ]

        indexes = [
            models.Index(
                fields=[
                    "school",
                    "enrollment",
                    "transaction_date",
                ]
            ),
        ]

    def clean(self):
        errors = {}

        if (
            self.enrollment_id
            and self.school_id
            and self.enrollment.school_id
            != self.school_id
        ):
            errors["enrollment"] = (
                "Enrollment belongs "
                "to another school."
            )

        if (
            self.invoice_id
            and self.invoice.enrollment_id
            != self.enrollment_id
        ):
            errors["invoice"] = (
                "Invoice belongs to a "
                "different enrollment."
            )

        if (
            self.payment_id
            and self.payment.enrollment_id
            != self.enrollment_id
        ):
            errors["payment"] = (
                "Payment belongs to a "
                "different enrollment."
            )

        if errors:
            raise ValidationError(
                errors
            )

    def __str__(self):
        return (
            f"{self.reference}: "
            f"D {self.debit} "
            f"C {self.credit}"
        )


class Receipt(SchoolOwnedModel):
    """
    Immutable-style receipt snapshot.
    """

    receipt_number = models.CharField(
        max_length=100,
    )

    payment = models.OneToOneField(
        Payment,
        on_delete=models.PROTECT,
        related_name="receipt",
    )

    snapshot = models.JSONField(
        default=dict,
    )

    issued_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="receipts_issued",
    )

    issued_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "school",
                    "receipt_number",
                ],
                name=(
                    "unique_receipt_number_"
                    "per_school"
                ),
            ),
        ]

    def clean(self):
        if (
            self.payment_id
            and self.school_id
            and self.payment.school_id
            != self.school_id
        ):
            raise ValidationError(
                {
                    "payment": (
                        "Payment belongs "
                        "to another school."
                    )
                }
            )

    def __str__(self):
        return self.receipt_number