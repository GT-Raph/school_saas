from django.contrib import admin

from .models import (
    School,
    SchoolBranding,
    SchoolDomain,
    SchoolMembership,
    SchoolRole,
)


@admin.register(
    SchoolBranding
)
class SchoolBrandingAdmin(
    admin.ModelAdmin
):
    list_display = (
        "school",
        "primary_color",
        "accent_color",
        "updated_at",
    )


@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "slug",
        "status",
        "currency",
        "created_at",
    )

    search_fields = (
        "name",
        "slug",
    )

    list_filter = (
        "status",
    )


@admin.register(SchoolDomain)
class SchoolDomainAdmin(admin.ModelAdmin):
    list_display = (
        "domain",
        "school",
        "is_primary",
        "is_verified",
    )

    search_fields = (
        "domain",
        "school__name",
    )


@admin.register(SchoolRole)
class SchoolRoleAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "code",
        "school",
    )

    filter_horizontal = (
        "permissions",
    )


@admin.register(SchoolMembership)
class SchoolMembershipAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "school",
        "is_active",
        "created_at",
    )

    filter_horizontal = (
        "roles",
    )

    search_fields = (
        "user__username",
        "user__email",
        "school__name",
    )