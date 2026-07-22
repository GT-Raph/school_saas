from django.contrib import admin

from .models import (
    Guardian,
    StudentGuardian,
)


@admin.register(Guardian)
class GuardianAdmin(admin.ModelAdmin):
    list_display = (
        "first_name",
        "last_name",
        "phone_number",
        "school",
        "is_active",
    )

    list_filter = (
        "school",
        "is_active",
    )

    search_fields = (
        "first_name",
        "last_name",
        "phone_number",
        "email",
    )


@admin.register(StudentGuardian)
class StudentGuardianAdmin(
    admin.ModelAdmin
):
    list_display = (
        "student",
        "guardian",
        "relationship",
        "is_primary_contact",
        "financially_responsible",
        "school",
    )

    list_filter = (
        "school",
        "relationship",
        "is_primary_contact",
    )