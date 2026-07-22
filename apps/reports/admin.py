from django.contrib import admin

from .models import (
    ReportCard,
    TermResult,
)


@admin.register(TermResult)
class TermResultAdmin(
    admin.ModelAdmin
):
    list_display = (
        "enrollment",
        "term",
        "average_score",
        "failed_subjects",
        "attendance_percentage",
        "status",
        "school",
    )

    list_filter = (
        "school",
        "term",
        "status",
    )

    search_fields = (
        "enrollment__student__admission_number",
        "enrollment__student__first_name",
        "enrollment__student__last_name",
    )

    readonly_fields = (
        "average_score",
        "total_subjects",
        "failed_subjects",
        "attendance_percentage",
        "calculated_at",
        "approved_by",
        "approved_at",
        "published_by",
        "published_at",
    )


@admin.register(ReportCard)
class ReportCardAdmin(
    admin.ModelAdmin
):
    list_display = (
        "report_number",
        "term_result",
        "status",
        "generated_at",
        "published_at",
        "school",
    )

    list_filter = (
        "school",
        "status",
    )

    search_fields = (
        "report_number",
        "term_result__enrollment__student__admission_number",
        "term_result__enrollment__student__first_name",
        "term_result__enrollment__student__last_name",
    )

    readonly_fields = (
        "snapshot",
        "generated_at",
        "published_by",
        "published_at",
    )