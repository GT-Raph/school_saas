import uuid
from decimal import Decimal

from django.core.exceptions import (
    ValidationError,
)
from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from apps.audit.models import AuditEvent

from .models import (
    FinancialAdjustment,
    InvoiceItem,
    LedgerEntry,
    Payment,
    PaymentAllocation,
    PaymentReversal,
    Receipt,
    StudentInvoice,
)


def _money(value):
    return Decimal(value).quantize(
        Decimal("0.01")
    )


def generate_invoice_number(
    academic_year,
):
    year = (
        academic_year.name
        .replace("/", "")
        .replace(" ", "")
    )

    return (
        f"INV-{year}-"
        f"{uuid.uuid4().hex[:8].upper()}"
    )


def generate_payment_number():
    return (
        f"PAY-"
        f"{uuid.uuid4().hex[:10].upper()}"
    )


def generate_receipt_number():
    return (
        f"RCT-"
        f"{uuid.uuid4().hex[:10].upper()}"
    )


def get_invoice_balance(invoice):
    totals = (
        invoice.ledger_entries.aggregate(
            debit=Sum("debit"),
            credit=Sum("credit"),
        )
    )

    debit = (
        totals["debit"]
        or Decimal("0")
    )

    credit = (
        totals["credit"]
        or Decimal("0")
    )

    return _money(
        debit - credit
    )


def get_enrollment_balance(
    enrollment,
):
    totals = (
        enrollment.ledger_entries.aggregate(
            debit=Sum("debit"),
            credit=Sum("credit"),
        )
    )

    debit = (
        totals["debit"]
        or Decimal("0")
    )

    credit = (
        totals["credit"]
        or Decimal("0")
    )

    return _money(
        debit - credit
    )


def refresh_invoice_status(
    invoice,
):
    if (
        invoice.status
        == StudentInvoice.Status.VOID
    ):
        return invoice

    balance = get_invoice_balance(
        invoice
    )

    credits = (
        invoice.ledger_entries.aggregate(
            total=Sum("credit")
        )["total"]
        or Decimal("0")
    )

    if balance <= Decimal("0"):
        new_status = (
            StudentInvoice.Status.PAID
        )

    elif credits > Decimal("0"):
        new_status = (
            StudentInvoice
            .Status.PARTIALLY_PAID
        )

    else:
        new_status = (
            StudentInvoice.Status.ISSUED
        )

    if invoice.status != new_status:
        invoice.status = new_status

        invoice.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )

    return invoice


@transaction.atomic
def generate_invoice_from_fee_structure(
    *,
    school,
    enrollment,
    fee_structure,
    issue_date,
    due_date=None,
    issued_by=None,
):
    """
    Generate one invoice from a configured fee structure.

    The invoice begins as DRAFT.

    No ledger charge exists until issue_invoice()
    is called.
    """

    if (
        enrollment.school_id
        != school.id
    ):
        raise ValidationError(
            "Enrollment belongs to "
            "another school."
        )

    if (
        fee_structure.school_id
        != school.id
    ):
        raise ValidationError(
            "Fee structure belongs to "
            "another school."
        )

    if (
        fee_structure.status
        != fee_structure.Status.ACTIVE
    ):
        raise ValidationError(
            "Fee structure must be active."
        )

    if (
        enrollment.academic_year_id
        != fee_structure
        .academic_year_id
    ):
        raise ValidationError(
            "Enrollment academic year "
            "does not match fee structure."
        )

    if (
        enrollment.class_section
        .level_id
        != fee_structure.class_level_id
    ):
        raise ValidationError(
            "Student is not enrolled at "
            "the class level covered by "
            "this fee structure."
        )

    if not (
        fee_structure.items.exists()
    ):
        raise ValidationError(
            "Fee structure has no items."
        )

    billing_key = (
        f"{enrollment.id}:"
        f"{fee_structure.id}"
    ) 
    
    invoice = StudentInvoice(
        school=school,

        invoice_number=(
            generate_invoice_number(
                enrollment.academic_year
            )
        ),

        billing_key=billing_key,

        enrollment=enrollment,

        term=fee_structure.term,

        fee_structure=(
            fee_structure
        ),

        issue_date=issue_date,

        due_date=due_date,

        gross_total=Decimal("0"),

        status=(
            StudentInvoice.Status.DRAFT
        ),

        issued_by=issued_by,
    )

    invoice.full_clean()
    invoice.save()

    total = Decimal("0")

    for structure_item in (
        fee_structure.items.all()
        .order_by("sequence")
    ):
        line_total = _money(
            structure_item.amount
        )

        item = InvoiceItem(
            school=school,
            invoice=invoice,
            fee_category=(
                structure_item.category
            ),
            description=(
                structure_item.description
                or structure_item
                .category.name
            ),
            quantity=Decimal("1"),
            unit_amount=(
                structure_item.amount
            ),
            line_total=line_total,
        )

        item.full_clean()
        item.save()

        total += line_total

    invoice.gross_total = _money(
        total
    )

    invoice.full_clean()
    invoice.save(
        update_fields=[
            "gross_total",
            "updated_at",
        ]
    )

    return invoice


@transaction.atomic
def issue_invoice(
    *,
    invoice,
    user,
):
    if (
        invoice.status
        != StudentInvoice.Status.DRAFT
    ):
        raise ValidationError(
            "Only draft invoices "
            "can be issued."
        )

    if (
        invoice.gross_total
        <= Decimal("0")
    ):
        raise ValidationError(
            "Invoice total must be "
            "greater than zero."
        )

    now = timezone.now()

    ledger = LedgerEntry(
        school=invoice.school,
        enrollment=invoice.enrollment,
        invoice=invoice,
        entry_type=(
            LedgerEntry.Type.INVOICE
        ),
        description=(
            f"Invoice "
            f"{invoice.invoice_number}"
        ),
        debit=invoice.gross_total,
        credit=Decimal("0"),
        transaction_date=now,
        reference=(
            f"INV:{invoice.id}"
        ),
        created_by=user,
    )

    ledger.full_clean()
    ledger.save()

    invoice.status = (
        StudentInvoice.Status.ISSUED
    )

    invoice.issued_by = user
    invoice.issued_at = now

    invoice.save(
        update_fields=[
            "status",
            "issued_by",
            "issued_at",
            "updated_at",
        ]
    )

    AuditEvent.objects.create(
        school=invoice.school,
        actor=user,
        action="invoice_issued",
        object_type="StudentInvoice",
        object_id=str(
            invoice.id
        ),
        changes={
            "invoice_number": (
                invoice.invoice_number
            ),
            "gross_total": str(
                invoice.gross_total
            ),
        },
    )

    return invoice


@transaction.atomic
def record_payment(
    *,
    school,
    enrollment,
    amount,
    method,
    paid_at,
    allocations,
    recorded_by,
    payer_name="",
    reference="",
    external_reference="",
    notes="",
):
    """
    Example allocations:

    [
        {
            "invoice": invoice_1,
            "amount": Decimal("1000"),
        },
        {
            "invoice": invoice_2,
            "amount": Decimal("500"),
        }
    ]
    """

    amount = _money(amount)

    if amount <= Decimal("0"):
        raise ValidationError(
            "Payment amount must "
            "be greater than zero."
        )

    allocation_total = sum(
        (
            _money(
                item["amount"]
            )
            for item in allocations
        ),
        Decimal("0"),
    )

    allocation_total = _money(
        allocation_total
    )

    if allocation_total != amount:
        raise ValidationError(
            (
                "Payment allocations must "
                f"equal payment amount. "
                f"Payment: {amount}, "
                f"allocated: "
                f"{allocation_total}."
            )
        )

    for item in allocations:
        invoice = item["invoice"]

        if (
            invoice.school_id
            != school.id
        ):
            raise ValidationError(
                "Invoice belongs to "
                "another school."
            )

        if (
            invoice.enrollment_id
            != enrollment.id
        ):
            raise ValidationError(
                "Invoice belongs to a "
                "different enrollment."
            )

        if invoice.status in {
            StudentInvoice.Status.DRAFT,
            StudentInvoice.Status.VOID,
        }:
            raise ValidationError(
                (
                    f"Invoice "
                    f"{invoice.invoice_number} "
                    "cannot receive payment."
                )
            )

        requested = _money(
            item["amount"]
        )

        balance = get_invoice_balance(
            invoice
        )

        if requested > balance:
            raise ValidationError(
                (
                    f"Allocation to "
                    f"{invoice.invoice_number} "
                    f"exceeds outstanding "
                    f"balance of {balance}."
                )
            )

    payment = Payment(
        school=school,
        payment_number=(
            generate_payment_number()
        ),
        enrollment=enrollment,
        amount=amount,
        method=method,
        status=(
            Payment.Status.CONFIRMED
        ),
        paid_at=paid_at,
        payer_name=payer_name,
        reference=reference,
        external_reference=(
            external_reference
        ),
        notes=notes,
        recorded_by=recorded_by,
        confirmed_by=recorded_by,
        confirmed_at=timezone.now(),
    )

    payment.full_clean()
    payment.save()

    for index, item in enumerate(
        allocations,
        start=1,
    ):
        invoice = item["invoice"]

        allocated_amount = _money(
            item["amount"]
        )

        allocation = PaymentAllocation(
            school=school,
            payment=payment,
            invoice=invoice,
            amount=allocated_amount,
        )

        allocation.full_clean()
        allocation.save()

        ledger = LedgerEntry(
            school=school,
            enrollment=enrollment,
            invoice=invoice,
            payment=payment,
            entry_type=(
                LedgerEntry.Type.PAYMENT
            ),
            description=(
                f"Payment "
                f"{payment.payment_number} "
                f"allocated to "
                f"{invoice.invoice_number}"
            ),
            debit=Decimal("0"),
            credit=allocated_amount,
            transaction_date=paid_at,
            reference=(
                f"PAY:{payment.id}:"
                f"{index}"
            ),
            created_by=recorded_by,
        )

        ledger.full_clean()
        ledger.save()

        refresh_invoice_status(
            invoice
        )

    AuditEvent.objects.create(
        school=school,
        actor=recorded_by,
        action="payment_recorded",
        object_type="Payment",
        object_id=str(
            payment.id
        ),
        changes={
            "payment_number": (
                payment.payment_number
            ),
            "amount": str(
                payment.amount
            ),
            "method": (
                payment.method
            ),
        },
    )

    return payment


@transaction.atomic
def apply_financial_adjustment(
    *,
    invoice,
    adjustment_type,
    amount,
    reason,
    approved_by,
):
    amount = _money(amount)

    if amount <= Decimal("0"):
        raise ValidationError(
            "Adjustment amount must "
            "be greater than zero."
        )

    if invoice.status in {
        StudentInvoice.Status.DRAFT,
        StudentInvoice.Status.VOID,
    }:
        raise ValidationError(
            "Adjustments may only be "
            "applied to issued invoices."
        )

    balance = get_invoice_balance(
        invoice
    )

    if amount > balance:
        raise ValidationError(
            (
                "Adjustment cannot exceed "
                f"outstanding balance "
                f"of {balance}."
            )
        )

    adjustment = FinancialAdjustment(
        school=invoice.school,
        invoice=invoice,
        adjustment_type=(
            adjustment_type
        ),
        amount=amount,
        reason=reason,
        status=(
            FinancialAdjustment
            .Status.APPROVED
        ),
        approved_by=approved_by,
        approved_at=timezone.now(),
    )

    adjustment.full_clean()
    adjustment.save()

    type_map = {
        FinancialAdjustment.Type.DISCOUNT:
            LedgerEntry.Type.DISCOUNT,

        FinancialAdjustment.Type.SCHOLARSHIP:
            LedgerEntry.Type.SCHOLARSHIP,

        FinancialAdjustment.Type.WAIVER:
            LedgerEntry.Type.WAIVER,

        FinancialAdjustment.Type.CREDIT:
            LedgerEntry.Type.CREDIT,
    }

    ledger = LedgerEntry(
        school=invoice.school,
        enrollment=invoice.enrollment,
        invoice=invoice,
        adjustment=adjustment,
        entry_type=(
            type_map[
                adjustment_type
            ]
        ),
        description=(
            f"{adjustment.get_adjustment_type_display()} "
            f"on {invoice.invoice_number}"
        ),
        debit=Decimal("0"),
        credit=amount,
        transaction_date=(
            timezone.now()
        ),
        reference=(
            f"ADJ:{adjustment.id}"
        ),
        created_by=approved_by,
    )

    ledger.full_clean()
    ledger.save()

    refresh_invoice_status(
        invoice
    )

    AuditEvent.objects.create(
        school=invoice.school,
        actor=approved_by,
        action=(
            "financial_adjustment_applied"
        ),
        object_type=(
            "FinancialAdjustment"
        ),
        object_id=str(
            adjustment.id
        ),
        changes={
            "invoice": (
                invoice.invoice_number
            ),
            "type": (
                adjustment_type
            ),
            "amount": str(
                amount
            ),
            "reason": reason,
        },
    )

    return adjustment


@transaction.atomic
def reverse_payment(
    *,
    payment,
    reason,
    reversed_by,
):
    if (
        payment.status
        != Payment.Status.CONFIRMED
    ):
        raise ValidationError(
            "Only confirmed payments "
            "can be reversed."
        )

    if hasattr(
        payment,
        "reversal",
    ):
        raise ValidationError(
            "This payment has already "
            "been reversed."
        )

    now = timezone.now()

    reversal = PaymentReversal(
        school=payment.school,
        payment=payment,
        reason=reason,
        reversed_by=reversed_by,
        reversed_at=now,
    )

    reversal.full_clean()
    reversal.save()

    allocations = (
        payment.allocations
        .select_related(
            "invoice"
        )
        .all()
    )

    for index, allocation in enumerate(
        allocations,
        start=1,
    ):
        ledger = LedgerEntry(
            school=payment.school,
            enrollment=payment.enrollment,
            invoice=allocation.invoice,
            payment=payment,
            entry_type=(
                LedgerEntry.Type
                .PAYMENT_REVERSAL
            ),
            description=(
                f"Reversal of payment "
                f"{payment.payment_number}"
            ),
            debit=allocation.amount,
            credit=Decimal("0"),
            transaction_date=now,
            reference=(
                f"PAYREV:"
                f"{payment.id}:"
                f"{index}"
            ),
            created_by=reversed_by,
        )

        ledger.full_clean()
        ledger.save()

        refresh_invoice_status(
            allocation.invoice
        )

    payment.status = (
        Payment.Status.REVERSED
    )

    payment.save(
        update_fields=[
            "status",
            "updated_at",
        ]
    )

    AuditEvent.objects.create(
        school=payment.school,
        actor=reversed_by,
        action="payment_reversed",
        object_type="Payment",
        object_id=str(
            payment.id
        ),
        changes={
            "payment_number": (
                payment.payment_number
            ),
            "amount": str(
                payment.amount
            ),
            "reason": reason,
        },
    )

    return reversal


@transaction.atomic
def reverse_financial_adjustment(
    *,
    adjustment,
    reason,
    reversed_by,
):
    if (
        adjustment.status
        != FinancialAdjustment
        .Status.APPROVED
    ):
        raise ValidationError(
            "Only approved adjustments "
            "can be reversed."
        )

    invoice = (
        adjustment.invoice
    )

    now = timezone.now()

    ledger = LedgerEntry(
        school=adjustment.school,
        enrollment=invoice.enrollment,
        invoice=invoice,
        adjustment=adjustment,
        entry_type=(
            LedgerEntry.Type
            .ADJUSTMENT_REVERSAL
        ),
        description=(
            f"Reversal of "
            f"{adjustment.get_adjustment_type_display()}"
        ),
        debit=adjustment.amount,
        credit=Decimal("0"),
        transaction_date=now,
        reference=(
            f"ADJREV:{adjustment.id}"
        ),
        created_by=reversed_by,
    )

    ledger.full_clean()
    ledger.save()

    adjustment.status = (
        FinancialAdjustment
        .Status.REVERSED
    )

    adjustment.reversed_at = now
    adjustment.reversed_by = (
        reversed_by
    )
    adjustment.reversal_reason = (
        reason
    )

    adjustment.save(
        update_fields=[
            "status",
            "reversed_at",
            "reversed_by",
            "reversal_reason",
            "updated_at",
        ]
    )

    refresh_invoice_status(
        invoice
    )

    AuditEvent.objects.create(
        school=adjustment.school,
        actor=reversed_by,
        action=(
            "financial_adjustment_reversed"
        ),
        object_type=(
            "FinancialAdjustment"
        ),
        object_id=str(
            adjustment.id
        ),
        changes={
            "amount": str(
                adjustment.amount
            ),
            "reason": reason,
        },
    )

    return adjustment


@transaction.atomic
def generate_receipt(
    *,
    payment,
    issued_by,
):
    if (
        payment.status
        != Payment.Status.CONFIRMED
    ):
        raise ValidationError(
            "Only confirmed payments "
            "can have valid receipts."
        )

    existing = getattr(
        payment,
        "receipt",
        None,
    )

    if existing:
        return existing

    allocations = (
        payment.allocations
        .select_related(
            "invoice"
        )
        .all()
    )

    snapshot = {
        "payment_number": (
            payment.payment_number
        ),

        "student": {
            "admission_number": (
                payment.enrollment
                .student
                .admission_number
            ),

            "name": (
                payment.enrollment
                .student
                .full_name
            ),
        },

        "amount": str(
            payment.amount
        ),

        "method": (
            payment.method
        ),

        "paid_at": (
            payment.paid_at.isoformat()
        ),

        "payer_name": (
            payment.payer_name
        ),

        "reference": (
            payment.reference
        ),

        "allocations": [
            {
                "invoice": (
                    allocation.invoice
                    .invoice_number
                ),

                "amount": str(
                    allocation.amount
                ),
            }
            for allocation
            in allocations
        ],
    }

    receipt = Receipt(
        school=payment.school,
        receipt_number=(
            generate_receipt_number()
        ),
        payment=payment,
        snapshot=snapshot,
        issued_by=issued_by,
    )

    receipt.full_clean()
    receipt.save()

    return receipt

@transaction.atomic
def bulk_generate_invoices(
    *,
    fee_structure,
    issue_date,
    due_date=None,
    issued_by=None,
    auto_issue=False,
):
    """
    Generate invoices for all active enrollments
    at the fee structure's class level.

    Existing billing keys are skipped.
    """

    enrollments = (
        fee_structure
        .academic_year
        .enrollments
        .filter(
            school=(
                fee_structure.school
            ),
            class_section__level=(
                fee_structure
                .class_level
            ),
            status=(
                "active"
            ),
        )
        .select_related(
            "student",
            "class_section",
            "academic_year",
        )
    )

    created = []

    skipped = []

    for enrollment in enrollments:

        billing_key = (
            f"{enrollment.id}:"
            f"{fee_structure.id}"
        )

        exists = (
            StudentInvoice.objects
            .filter(
                school=(
                    fee_structure.school
                ),
                billing_key=(
                    billing_key
                ),
            )
            .exclude(
                status=(
                    StudentInvoice
                    .Status.VOID
                )
            )
            .exists()
        )

        if exists:

            skipped.append(
                enrollment
            )

            continue

        invoice = (
            generate_invoice_from_fee_structure(
                school=(
                    fee_structure.school
                ),

                enrollment=(
                    enrollment
                ),

                fee_structure=(
                    fee_structure
                ),

                issue_date=(
                    issue_date
                ),

                due_date=(
                    due_date
                ),

                issued_by=(
                    issued_by
                ),
            )
        )

        if auto_issue:

            issue_invoice(
                invoice=invoice,
                user=issued_by,
            )

        created.append(
            invoice
        )

    return {
        "created": created,
        "skipped": skipped,
    }

@transaction.atomic
def void_invoice(
    *,
    invoice,
    reason,
    voided_by,
):
    if (
        invoice.status
        == StudentInvoice.Status.DRAFT
    ):
        invoice.status = (
            StudentInvoice.Status.VOID
        )

        invoice.notes = (
            f"{invoice.notes}\n"
            f"VOID: {reason}"
        ).strip()

        invoice.save(
            update_fields=[
                "status",
                "notes",
                "updated_at",
            ]
        )

        return invoice

    balance = get_invoice_balance(
        invoice
    )

    if balance != invoice.gross_total:
        raise ValidationError(
            (
                "An invoice with payments "
                "or adjustments cannot be "
                "directly voided. Reverse "
                "those transactions first."
            )
        )

    reversal = LedgerEntry(
        school=invoice.school,

        enrollment=(
            invoice.enrollment
        ),

        invoice=invoice,

        entry_type=(
            LedgerEntry.Type.CREDIT
        ),

        description=(
            f"Void invoice "
            f"{invoice.invoice_number}: "
            f"{reason}"
        ),

        debit=Decimal("0"),

        credit=(
            invoice.gross_total
        ),

        transaction_date=(
            timezone.now()
        ),

        reference=(
            f"INVVOID:{invoice.id}"
        ),

        created_by=voided_by,
    )

    reversal.full_clean()
    reversal.save()

    invoice.status = (
        StudentInvoice.Status.VOID
    )

    invoice.notes = (
        f"{invoice.notes}\n"
        f"VOID: {reason}"
    ).strip()

    invoice.save(
        update_fields=[
            "status",
            "notes",
            "updated_at",
        ]
    )

    AuditEvent.objects.create(
        school=invoice.school,

        actor=voided_by,

        action="invoice_voided",

        object_type=(
            "StudentInvoice"
        ),

        object_id=str(
            invoice.id
        ),

        changes={
            "invoice_number": (
                invoice.invoice_number
            ),

            "amount": str(
                invoice.gross_total
            ),

            "reason": reason,
        },
    )

    return invoice

def get_student_statement(
    *,
    enrollment,
):
    entries = (
        enrollment.ledger_entries
        .select_related(
            "invoice",
            "payment",
            "adjustment",
        )
        .order_by(
            "transaction_date",
            "created_at",
        )
    )

    running_balance = Decimal(
        "0"
    )

    statement = []

    for entry in entries:
        running_balance += (
            entry.debit
            - entry.credit
        )

        statement.append(
            {
                "date": (
                    entry.transaction_date
                ),

                "reference": (
                    entry.reference
                ),

                "description": (
                    entry.description
                ),

                "debit": (
                    entry.debit
                ),

                "credit": (
                    entry.credit
                ),

                "balance": _money(
                    running_balance
                ),
            }
        )

    return statement