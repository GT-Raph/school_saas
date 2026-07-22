from django.contrib import admin

from .models import Staff


@admin.register(Staff)
class StaffAdmin(admin.ModelAdmin):
    list_display = (
        "employee_number",
        "first_name",
        "last_name",
        "job_title",
        "department",
        "school",
        "employment_status",
    )

    list_filter = (
        "school",
        "employment_status",
        "department",
    )

    search_fields = (
        "employee_number",
        "first_name",
        "middle_name",
        "last_name",
        "phone_number",
        "email",
    )