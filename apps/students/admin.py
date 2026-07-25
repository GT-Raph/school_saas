from django.contrib import admin

from .models import (
    Student,
    StudentImportBatch,
    StudentImportRow,
)


@admin.register(
    StudentImportBatch
)
class StudentImportBatchAdmin(
    admin.ModelAdmin
):

    list_display = (
        "original_filename",
        "school",
        "status",
        "total_rows",
        "valid_rows",
        "invalid_rows",
        "created_at",
    )

    readonly_fields = (
        "original_filename",
        "school",
        "status",
        "total_rows",
        "valid_rows",
        "invalid_rows",
        "uploaded_by",
        "completed_at",
        "error_message",
        "created_at",
        "updated_at",
    )

    def has_add_permission(
        self,
        request,
    ):
        return False


@admin.register(
    StudentImportRow
)
class StudentImportRowAdmin(
    admin.ModelAdmin
):

    list_display = (
        "batch",
        "row_number",
        "is_valid",
        "imported_student",
        "school",
    )

    readonly_fields = (
        "batch",
        "row_number",
        "raw_data",
        "normalized_data",
        "errors",
        "is_valid",
        "imported_student",
        "school",
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


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = (
        "admission_number",
        "first_name",
        "last_name",
        "school",
        "status",
        "admission_date",
    )

    list_filter = (
        "school",
        "status",
        "gender",
    )

    search_fields = (
        "admission_number",
        "first_name",
        "middle_name",
        "last_name",
        "phone_number",
        "email",
    )

    readonly_fields = (
        "id",
        "created_at",
        "updated_at",
    )