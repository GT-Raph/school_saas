from django.contrib import admin

from .models import SchoolSubscription, SubscriptionPlan


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "code",
        "active_student_limit",
        "admin_user_limit",
        "is_active",
    )


@admin.register(SchoolSubscription)
class SchoolSubscriptionAdmin(admin.ModelAdmin):
    list_display = (
        "school",
        "plan",
        "status",
        "period_start",
        "period_end",
        "grace_period_end",
    )

    list_filter = (
        "status",
        "plan",
    )