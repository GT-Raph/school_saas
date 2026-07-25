from decimal import Decimal

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.http import HttpResponseNotAllowed
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)

from apps.accounts.decorators import (
    school_permission_required,
)
from apps.academics.models import Enrollment
from apps.finance.models import (
    Receipt,
    StudentInvoice,
)
from apps.finance.services import (
    bulk_generate_invoices,
    generate_receipt,
    get_enrollment_balance,
    get_invoice_balance,
    get_student_statement,
    issue_invoice,
    record_payment,
)
from apps.subscriptions.decorators import (
    subscription_write_required,
)

from .finance_forms import (
    BulkInvoiceForm,
    PaymentEntryForm,
)


@school_permission_required(
    "finance.view_studentinvoice"
)
def finance_invoices(request):
    invoices = (
        StudentInvoice.objects
        .for_school(request.school)
        .select_related(
            "enrollment__student",
            "term",
        )
        .order_by(
            "-issue_date",
            "-created_at",
        )
    )

    query = request.GET.get(
        "q",
        "",
    ).strip()

    if query:
        invoices = invoices.filter(
            Q(
                invoice_number__icontains=query
            )
            | Q(
                enrollment__student__admission_number__icontains=query
            )
            | Q(
                enrollment__student__first_name__icontains=query
            )
            | Q(
                enrollment__student__last_name__icontains=query
            )
        )

    rows = []

    for invoice in invoices[:300]:
        rows.append(
            {
                "invoice": invoice,
                "balance": get_invoice_balance(
                    invoice
                ),
            }
        )

    return render(
        request,
        "portal/finance/invoices.html",
        {
            "rows": rows,
            "query": query,
        },
    )


@subscription_write_required
@school_permission_required(
    "finance.issue_student_invoice"
)
def finance_bulk_invoices(request):
    if request.method == "POST":
        form = BulkInvoiceForm(
            request.POST,
            school=request.school,
        )

        if form.is_valid():
            try:
                result = bulk_generate_invoices(
                    fee_structure=(
                        form.cleaned_data[
                            "fee_structure"
                        ]
                    ),
                    issue_date=(
                        form.cleaned_data[
                            "issue_date"
                        ]
                    ),
                    due_date=(
                        form.cleaned_data[
                            "due_date"
                        ]
                    ),
                    issued_by=request.user,
                    auto_issue=(
                        form.cleaned_data[
                            "auto_issue"
                        ]
                    ),
                )

            except ValidationError as exc:
                form.add_error(
                    None,
                    exc.messages,
                )

            else:
                messages.success(
                    request,
                    (
                        f"{len(result['created'])} "
                        "invoices created. "
                        f"{len(result['skipped'])} "
                        "existing invoices skipped."
                    ),
                )

                return redirect(
                    "portal:finance-invoices"
                )

    else:
        form = BulkInvoiceForm(
            school=request.school,
        )

    return render(
        request,
        "portal/form.html",
        {
            "title": (
                "Generate Student Invoices"
            ),
            "form": form,
            "submit_label": (
                "Generate Invoices"
            ),
        },
    )


@subscription_write_required
@school_permission_required(
    "finance.issue_student_invoice"
)
def finance_issue_invoice(
    request,
    invoice_id,
):
    if request.method != "POST":
        return HttpResponseNotAllowed(
            ["POST"]
        )

    invoice = get_object_or_404(
        StudentInvoice.objects.for_school(
            request.school
        ),
        id=invoice_id,
    )

    try:
        issue_invoice(
            invoice=invoice,
            user=request.user,
        )

    except ValidationError as exc:
        messages.error(
            request,
            " ".join(
                exc.messages
            ),
        )

    else:
        messages.success(
            request,
            (
                f"Invoice "
                f"{invoice.invoice_number} "
                "issued."
            ),
        )

    return redirect(
        "portal:finance-invoices"
    )


@subscription_write_required
@school_permission_required(
    "finance.record_student_payment"
)
def finance_record_payment(request):
    if request.method == "POST":
        form = PaymentEntryForm(
            request.POST,
            school=request.school,
        )

        if form.is_valid():
            invoice = (
                form.cleaned_data[
                    "invoice"
                ]
            )

            enrollment = (
                form.cleaned_data[
                    "enrollment"
                ]
            )

            try:
                payment = record_payment(
                    school=request.school,
                    enrollment=enrollment,
                    amount=(
                        form.cleaned_data[
                            "amount"
                        ]
                    ),
                    method=(
                        form.cleaned_data[
                            "method"
                        ]
                    ),
                    paid_at=(
                        form.cleaned_data[
                            "paid_at"
                        ]
                    ),
                    allocations=[
                        {
                            "invoice": invoice,
                            "amount": (
                                form.cleaned_data[
                                    "amount"
                                ]
                            ),
                        }
                    ],
                    recorded_by=request.user,
                    payer_name=(
                        form.cleaned_data[
                            "payer_name"
                        ]
                    ),
                    reference=(
                        form.cleaned_data[
                            "reference"
                        ]
                    ),
                    notes=(
                        form.cleaned_data[
                            "notes"
                        ]
                    ),
                )

                receipt = generate_receipt(
                    payment=payment,
                    issued_by=request.user,
                )

            except ValidationError as exc:
                form.add_error(
                    None,
                    exc.messages,
                )

            else:
                messages.success(
                    request,
                    (
                        "Payment recorded. "
                        f"Receipt: "
                        f"{receipt.receipt_number}"
                    ),
                )

                return redirect(
                    "portal:finance-receipt",
                    receipt_id=receipt.id,
                )

    else:
        form = PaymentEntryForm(
            school=request.school,
        )

    return render(
        request,
        "portal/form.html",
        {
            "title": "Record Payment",
            "form": form,
            "submit_label": (
                "Record Payment"
            ),
        },
    )


@school_permission_required(
    "finance.view_receipt"
)
def finance_receipt(
    request,
    receipt_id,
):
    receipt = get_object_or_404(
        Receipt.objects
        .for_school(request.school)
        .select_related(
            "payment__enrollment__student"
        ),
        id=receipt_id,
    )

    return render(
        request,
        "portal/finance/receipt.html",
        {
            "receipt": receipt,
        },
    )


@school_permission_required(
    "finance.view_ledgerentry"
)
def finance_student_accounts(request):
    enrollments = (
        Enrollment.objects
        .for_school(request.school)
        .filter(
            status=Enrollment.Status.ACTIVE
        )
        .select_related(
            "student",
            "class_section__level",
        )
        .order_by(
            "student__last_name",
            "student__first_name",
        )
    )

    query = request.GET.get(
        "q",
        "",
    ).strip()

    if query:
        enrollments = enrollments.filter(
            Q(
                student__admission_number__icontains=query
            )
            | Q(
                student__first_name__icontains=query
            )
            | Q(
                student__last_name__icontains=query
            )
        )

    rows = []

    for enrollment in enrollments[:300]:
        rows.append(
            {
                "enrollment": enrollment,
                "balance": (
                    get_enrollment_balance(
                        enrollment
                    )
                ),
            }
        )

    return render(
        request,
        (
            "portal/finance/"
            "student_accounts.html"
        ),
        {
            "rows": rows,
            "query": query,
        },
    )


@school_permission_required(
    "finance.view_ledgerentry"
)
def finance_student_statement(
    request,
    enrollment_id,
):
    enrollment = get_object_or_404(
        Enrollment.objects
        .for_school(request.school)
        .select_related(
            "student",
            "class_section__level",
            "academic_year",
        ),
        id=enrollment_id,
    )

    statement = get_student_statement(
        enrollment=enrollment,
    )

    balance = get_enrollment_balance(
        enrollment
    )

    return render(
        request,
        (
            "portal/finance/"
            "student_statement.html"
        ),
        {
            "enrollment": enrollment,
            "statement": statement,
            "balance": balance,
        },
    )


@school_permission_required(
    "finance.view_studentinvoice"
)
def finance_debtors(request):
    enrollments = (
        Enrollment.objects
        .for_school(request.school)
        .filter(
            status=Enrollment.Status.ACTIVE
        )
        .select_related(
            "student",
            "class_section__level",
        )
    )

    debtors = []

    total_outstanding = Decimal(
        "0.00"
    )

    for enrollment in enrollments:
        balance = get_enrollment_balance(
            enrollment
        )

        if balance > 0:
            debtors.append(
                {
                    "enrollment": enrollment,
                    "balance": balance,
                }
            )

            total_outstanding += balance

    debtors.sort(
        key=lambda item: item["balance"],
        reverse=True,
    )

    return render(
        request,
        "portal/finance/debtors.html",
        {
            "debtors": debtors,
            "total_outstanding": (
                total_outstanding
            ),
        },
    )