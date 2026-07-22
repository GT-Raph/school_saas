from django.contrib import admin

from .models import (
    Assessment,
    AssessmentCategory,
    AssessmentScheme,
    GradeBand,
    GradeScale,
    OfferingAssessmentPlan,
    Score,
    SubjectResult,
)


class AssessmentCategoryInline(
    admin.TabularInline
):
    model = AssessmentCategory
    extra = 1


@admin.register(AssessmentScheme)
class AssessmentSchemeAdmin(
    admin.ModelAdmin
):
    list_display = (
        "name",
        "academic_year",
        "school",
        "is_active",
    )

    list_filter = (
        "school",
        "academic_year",
        "is_active",
    )

    inlines = [
        AssessmentCategoryInline,
    ]


class GradeBandInline(
    admin.TabularInline
):
    model = GradeBand
    extra = 1


@admin.register(GradeScale)
class GradeScaleAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "code",
        "school",
        "is_active",
    )

    inlines = [
        GradeBandInline,
    ]


@admin.register(OfferingAssessmentPlan)
class OfferingAssessmentPlanAdmin(
    admin.ModelAdmin
):
    list_display = (
        "offering",
        "term",
        "scheme",
        "grade_scale",
        "school",
    )

    list_filter = (
        "school",
        "term",
    )


@admin.register(Assessment)
class AssessmentAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "assessment_plan",
        "category",
        "max_score",
        "status",
        "school",
    )

    list_filter = (
        "school",
        "status",
        "category",
    )


@admin.register(Score)
class ScoreAdmin(admin.ModelAdmin):
    list_display = (
        "enrollment",
        "assessment",
        "raw_score",
        "is_absent",
        "school",
    )

    list_filter = (
        "school",
        "assessment",
        "is_absent",
    )

    search_fields = (
        "enrollment__student__first_name",
        "enrollment__student__last_name",
        "enrollment__student__admission_number",
    )


@admin.register(SubjectResult)
class SubjectResultAdmin(
    admin.ModelAdmin
):
    list_display = (
        "enrollment",
        "assessment_plan",
        "total_score",
        "grade",
        "status",
        "school",
    )

    list_filter = (
        "school",
        "status",
        "grade",
    )

    readonly_fields = (
        "total_score",
        "grade",
        "grade_label",
        "remark",
        "submitted_by",
        "submitted_at",
        "approved_by",
        "approved_at",
        "published_by",
        "published_at",
    )