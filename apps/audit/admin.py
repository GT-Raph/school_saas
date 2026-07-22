from django.contrib import admin

from .models import AuditEvent


@admin.register(AuditEvent)
class AuditEventAdmin(admin.ModelAdmin):
    list_display = (
        "action",
        "school",
        "actor",
        "object_type",
        "created_at",
    )

    list_filter = (
        "action",
        "school",
    )

    search_fields = (
        "action",
        "object_type",
        "object_id",
        "actor__username",
    )

    readonly_fields = (
        "id",
        "school",
        "actor",
        "action",
        "object_type",
        "object_id",
        "changes",
        "metadata",
        "ip_address",
        "created_at",
        "updated_at",
    )

    def has_add_permission(self, request):
        return False