from django.contrib import admin

from .models import (
    PromotionDecision,
    PromotionEvaluation,
    PromotionPolicy,
    PromotionSubjectRule,
)


class PromotionSubjectRuleInline(
    admin.TabularInline
):
    model = PromotionSubjectRule
    extra = 1


@admin.register(PromotionPolicy)
class PromotionPolicyAdmin(
    admin.ModelAdmin
):
    list_display = (
        "name",
        "academic_year",
        "class_level",
        "version",
        "minimum_overall_average",
        "maximum_failed_subjects",
        "minimum_attendance_percentage",
        "is_active",
        "school",
    )

    list_filter = (
        "school",
        "academic_year",
        "class_level",
        "is_active",
    )

    inlines = [
        PromotionSubjectRuleInline,
    ]


@admin.register(
    PromotionEvaluation
)
class PromotionEvaluationAdmin(
    admin.ModelAdmin
):
    list_display = (
        "enrollment",
        "annual_average",
        "failed_subjects",
        "attendance_percentage",
        "recommendation",
        "school",
        "evaluated_at",
    )

    list_filter = (
        "school",
        "recommendation",
        "policy",
    )

    readonly_fields = (
        "policy",
        "enrollment",
        "annual_average",
        "attendance_percentage",
        "failed_subjects",
        "recommendation",
        "reasons",
        "metrics",
        "evaluated_at",
    )


@admin.register(
    PromotionDecision
)
class PromotionDecisionAdmin(
    admin.ModelAdmin
):
    list_display = (
        "evaluation",
        "final_decision",
        "target_class_section",
        "approved_by",
        "approved_at",
        "executed_at",
        "school",
    )

    list_filter = (
        "school",
        "final_decision",
        "approved_at",
    )

    readonly_fields = (
        "evaluation",
        "approved_by",
        "approved_at",
        "executed_at",
        "resulting_enrollment",
    )