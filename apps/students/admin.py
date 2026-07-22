from django.contrib import admin

from .models import Student


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