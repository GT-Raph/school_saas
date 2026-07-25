from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        (
            "Platform",
            {
                "fields": (
                    "phone_number",
                    "is_platform_admin",
                    "must_change_password",
                )
            },
        ),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        (
            "Platform",
            {
                "fields": (
                    "phone_number",
                    "is_platform_admin",
                    "must_change_password",
                )
            },
        ),
    )

    list_display = (
        "username",
        "email",
        "first_name",
        "last_name",
        "is_platform_admin",
        "is_staff",
        "is_active",
    )