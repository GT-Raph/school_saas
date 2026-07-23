from django.urls import path

from apps.portal import admin_views

from . import views


app_name = "portal"


urlpatterns = [
    path(
        "",
        views.portal_home,
        name="home",
    ),

    path(
        "admin/",
        views.school_admin_dashboard,
        name="school-admin",
    ),

    path(
        "academic/",
        views.academic_dashboard,
        name="academic",
    ),

    path(
        "finance/",
        views.finance_dashboard,
        name="finance",
    ),

    path(
        "teacher/",
        views.teacher_dashboard,
        name="teacher",
    ),

    path(
        "parent/",
        views.parent_dashboard,
        name="parent",
    ),

    path(
        "student/",
        views.student_dashboard,
        name="student",
    ),

    # Students

    path(
        "students/",
        admin_views.student_list,
        name="student-list",
    ),

    path(
        "students/admit/",
        admin_views.student_admit,
        name="student-admit",
    ),

    path(
        "students/<uuid:student_id>/",
        admin_views.student_detail,
        name="student-detail",
    ),

    path(
        "students/<uuid:student_id>/edit/",
        admin_views.student_edit,
        name="student-edit",
    ),


    # Student Imports

    path(
        "students/import/",
        admin_views.student_import_upload,
        name="student-import",
    ),

    path(
        "students/import/<uuid:batch_id>/",
        admin_views.student_import_detail,
        name="student-import-detail",
    ),

    path(
        (
            "students/import/"
            "<uuid:batch_id>/confirm/"
        ),
        admin_views.student_import_confirm,
        name="student-import-confirm",
    ),


    # Guardians

    path(
        "guardians/",
        admin_views.guardian_list,
        name="guardian-list",
    ),

    path(
        "guardians/add/",
        admin_views.guardian_create,
        name="guardian-create",
    ),

    path(
        "guardians/link/",
        admin_views.guardian_link,
        name="guardian-link",
    ),


    # Staff

    path(
        "staff/",
        admin_views.staff_list,
        name="staff-list",
    ),

    path(
        "staff/add/",
        admin_views.staff_create,
        name="staff-create",
    ),

    path(
        "staff/<uuid:staff_id>/edit/",
        admin_views.staff_edit,
        name="staff-edit",
    ),


    # Admin Studio

    path(
        "settings/",
        admin_views.admin_studio,
        name="admin-studio",
    ),

    path(
        "settings/profile/",
        (
            admin_views
            .school_profile_settings
        ),
        name="school-profile-settings",
    ),

    path(
        "settings/branding/",
        (
            admin_views
            .school_branding_settings
        ),
        name="school-branding-settings",
    ),
]