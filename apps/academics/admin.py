from django.contrib import admin

from .models import (
    AcademicYear,
    ClassLevel,
    ClassSection,
    Enrollment,
    Subject,
    SubjectOffering,
    TeacherAssignment,
    Term,
)


@admin.register(AcademicYear)
class AcademicYearAdmin(
    admin.ModelAdmin
):
    list_display = (
        "name",
        "school",
        "starts_on",
        "ends_on",
        "status",
        "is_current",
    )

    list_filter = (
        "school",
        "status",
        "is_current",
    )


@admin.register(Term)
class TermAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "academic_year",
        "sequence",
        "school",
        "starts_on",
        "ends_on",
        "is_current",
    )

    list_filter = (
        "school",
        "academic_year",
        "is_current",
    )


@admin.register(ClassLevel)
class ClassLevelAdmin(
    admin.ModelAdmin
):
    list_display = (
        "name",
        "code",
        "order",
        "next_level",
        "is_graduating_level",
        "school",
    )

    list_filter = (
        "school",
        "is_active",
        "is_graduating_level",
    )


@admin.register(ClassSection)
class ClassSectionAdmin(
    admin.ModelAdmin
):
    list_display = (
        "level",
        "name",
        "code",
        "capacity",
        "school",
        "is_active",
    )

    list_filter = (
        "school",
        "level",
        "is_active",
    )


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "code",
        "school",
        "is_core",
        "is_active",
    )

    list_filter = (
        "school",
        "is_core",
        "is_active",
    )

    search_fields = (
        "name",
        "code",
    )


@admin.register(Enrollment)
class EnrollmentAdmin(
    admin.ModelAdmin
):
    list_display = (
        "student",
        "academic_year",
        "class_section",
        "status",
        "school",
    )

    list_filter = (
        "school",
        "academic_year",
        "class_section",
        "status",
    )

    search_fields = (
        "student__admission_number",
        "student__first_name",
        "student__last_name",
    )

@admin.register(SubjectOffering)
class SubjectOfferingAdmin(admin.ModelAdmin):
    list_display = (
        "subject",
        "class_section",
        "academic_year",
        "school",
        "is_active",
    )

    list_filter = (
        "school",
        "academic_year",
        "class_section",
        "is_active",
    )

    search_fields = (
        "subject__name",
        "class_section__name",
        "class_section__level__name",
    )


@admin.register(TeacherAssignment)
class TeacherAssignmentAdmin(admin.ModelAdmin):
    list_display = (
        "teacher",
        "offering",
        "starts_on",
        "ends_on",
        "is_primary",
        "is_active",
        "school",
    )

    list_filter = (
        "school",
        "is_primary",
        "is_active",
    )

    search_fields = (
        "teacher__first_name",
        "teacher__last_name",
        "teacher__employee_number",
        "offering__subject__name",
    )