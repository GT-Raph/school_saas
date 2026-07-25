from django.contrib import admin

from .models import (
    FeeCategory,
    FeeStructure,
    FeeStructureItem,
    FinancialAdjustment,
    InvoiceItem,
    LedgerEntry,
    Payment,
    PaymentAllocation,
    PaymentReversal,
    Receipt,
    StudentInvoice,
)


@admin.register(FeeCategory)
class FeeCategoryAdmin(
    admin.ModelAdmin
):
    list_display = (
        "name",
        "code",
        "school",
        "is_active",
    )

    list_filter = (
        "school",
        "is_active",
    )

    search_fields = (
        "name",
        "code",
    )


class FeeStructureItemInline(
    admin.TabularInline
):
    model = FeeStructureItem
    extra = 1


@admin.register(FeeStructure)
class FeeStructureAdmin(
    admin.ModelAdmin
):
    list_display = (
        "name",
        "academic_year",
        "term",
        "class_level",
        "status",
        "school",
    )

    list_filter = (
        "school",
        "academic_year",
        "term",
        "class_level",
        "status",
    )

    inlines = [
        FeeStructureItemInline,
    ]


class InvoiceItemInline(
    admin.TabularInline
):
    model = InvoiceItem
    extra = 0
    readonly_fields = (
        "fee_category",
        "description",
        "quantity",
        "unit_amount",
        "line_total",
    )

    can_delete = False


@admin.register(StudentInvoice)
class StudentInvoiceAdmin(
    admin.ModelAdmin
):
    list_display = (
        "invoice_number",
        "enrollment",
        "term",
        "gross_total",
        "status",
        "due_date",
        "school",
    )

    list_filter = (
        "school",
        "term",
        "status",
    )

    search_fields = (
        "invoice_number",
        "enrollment__student__admission_number",
        "enrollment__student__first_name",
        "enrollment__student__last_name",
    )

    readonly_fields = (
        "gross_total",
        "issued_by",
        "issued_at",
    )

    inlines = [
        InvoiceItemInline,
    ]
    def has_add_permission(
        self,
        request,
    ):
        return False
    
    def has_delete_permission(
        self,
        request,
        obj=None,
    ):
        return False


class PaymentAllocationInline(
    admin.TabularInline
):
    model = PaymentAllocation
    extra = 0
    readonly_fields = (
        "invoice",
        "amount",
    )

    can_delete = False


@admin.register(Payment)
class PaymentAdmin(
    admin.ModelAdmin
):
    list_display = (
        "payment_number",
        "enrollment",
        "amount",
        "method",
        "status",
        "paid_at",
        "school",
    )

    list_filter = (
        "school",
        "status",
        "method",
    )

    search_fields = (
        "payment_number",
        "reference",
        "external_reference",
        "enrollment__student__admission_number",
        "enrollment__student__first_name",
        "enrollment__student__last_name",
    )

    readonly_fields = (
        "payment_number",
        "status",
        "confirmed_by",
        "confirmed_at",
    )

    inlines = [
        PaymentAllocationInline,
    ]

    def has_delete_permission(
        self,
        request,
        obj=None,
    ):
        return False
    
    def has_add_permission(
        self,
        request,
    ):
        return False


@admin.register(FinancialAdjustment)
class FinancialAdjustmentAdmin(
    admin.ModelAdmin
):
    list_display = (
        "invoice",
        "adjustment_type",
        "amount",
        "status",
        "approved_by",
        "approved_at",
        "school",
    )

    list_filter = (
        "school",
        "adjustment_type",
        "status",
    )

    readonly_fields = (
        "approved_by",
        "approved_at",
        "reversed_at",
        "reversed_by",
        "reversal_reason",
    )

    def has_delete_permission(
        self,
        request,
        obj=None,
    ):
        return False
    
    def has_add_permission(
        self,
        request,
    ):
        return False


@admin.register(LedgerEntry)
class LedgerEntryAdmin(
    admin.ModelAdmin
):
    list_display = (
        "transaction_date",
        "enrollment",
        "entry_type",
        "description",
        "debit",
        "credit",
        "reference",
        "school",
    )

    list_filter = (
        "school",
        "entry_type",
    )

    search_fields = (
        "reference",
        "description",
        "enrollment__student__admission_number",
        "enrollment__student__first_name",
        "enrollment__student__last_name",
    )

    readonly_fields = (
        "id",
        "school",
        "enrollment",
        "invoice",
        "payment",
        "adjustment",
        "entry_type",
        "description",
        "debit",
        "credit",
        "transaction_date",
        "reference",
        "created_by",
        "created_at",
        "updated_at",
    )

    def has_add_permission(
        self,
        request,
    ):
        return False

    def has_delete_permission(
        self,
        request,
        obj=None,
    ):
        return False


@admin.register(Receipt)
class ReceiptAdmin(
    admin.ModelAdmin
):
    list_display = (
        "receipt_number",
        "payment",
        "issued_by",
        "issued_at",
        "school",
    )

    readonly_fields = (
        "receipt_number",
        "payment",
        "snapshot",
        "issued_by",
        "issued_at",
    )

    def has_add_permission(
        self,
        request,
    ):
        return False

    def has_delete_permission(
        self,
        request,
        obj=None,
    ):
        return False


@admin.register(PaymentReversal)
class PaymentReversalAdmin(
    admin.ModelAdmin
):
    list_display = (
        "payment",
        "reversed_by",
        "reversed_at",
        "school",
    )

    readonly_fields = (
        "payment",
        "reason",
        "reversed_by",
        "reversed_at",
    )

    def has_add_permission(
        self,
        request,
    ):
        return False

    def has_delete_permission(
        self,
        request,
        obj=None,
    ):
        return False