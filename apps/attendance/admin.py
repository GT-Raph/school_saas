from django.contrib import admin

from .models import (
    AttendanceRecord,
    AttendanceSession,
)


class AttendanceRecordInline(admin.TabularInline):
    model = AttendanceRecord
    extra = 0


@admin.register(AttendanceSession)
class AttendanceSessionAdmin(admin.ModelAdmin):
    list_display = (
        "attendance_date",
        "class_section",
        "term",
        "status",
        "taken_by",
        "school",
    )

    list_filter = (
        "school",
        "term",
        "status",
        "attendance_date",
    )

    inlines = [
        AttendanceRecordInline,
    ]


@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(admin.ModelAdmin):
    list_display = (
        "enrollment",
        "session",
        "status",
        "school",
    )

    list_filter = (
        "school",
        "status",
    )