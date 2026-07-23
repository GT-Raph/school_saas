from django.urls import path

from . import admin_views, teacher_views, finance_views

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

    path(
        "teacher/classes/",
        teacher_views.teacher_classes,
        name="teacher-classes",
    ),

    path(
        (
            "teacher/classes/"
            "<uuid:offering_id>/"
        ),
        teacher_views.teacher_class_detail,
        name="teacher-class-detail",
    ),

    path(
        (
            "teacher/classes/"
            "<uuid:offering_id>/"
            "attendance/"
            "<uuid:term_id>/"
        ),
        teacher_views.teacher_take_attendance,
        name="teacher-attendance",
    ),

    path(
        (
            "teacher/classes/"
            "<uuid:offering_id>/"
            "assessments/"
            "<uuid:term_id>/"
        ),
        teacher_views.teacher_assessments,
        name="teacher-assessments",
    ),

    path(
        (
            "teacher/assessments/"
            "<uuid:assessment_id>/"
            "scores/"
        ),
        teacher_views.teacher_enter_scores,
        name="teacher-enter-scores",
    ),

    path(
        (
            "teacher/results/"
            "<uuid:plan_id>/"
            "calculate-submit/"
        ),
        (
            teacher_views
            .teacher_calculate_submit_results
        ),
        name=(
            "teacher-calculate-"
            "submit-results"
        ),
    ),

      path(
        "finance/invoices/",
        finance_views.finance_invoices,
        name="finance-invoices",
    ),

    path(
        "finance/invoices/generate/",
        (
            finance_views
            .finance_bulk_invoices
        ),
        name="finance-bulk-invoices",
    ),

    path(
        (
            "finance/invoices/"
            "<uuid:invoice_id>/issue/"
        ),
        (
            finance_views
            .finance_issue_invoice
        ),
        name="finance-issue-invoice",
    ),

    path(
        "finance/payments/record/",
        (
            finance_views
            .finance_record_payment
        ),
        name="finance-record-payment",
    ),

    path(
        (
            "finance/receipts/"
            "<uuid:receipt_id>/"
        ),
        finance_views.finance_receipt,
        name="finance-receipt",
    ),

    path(
        "finance/accounts/",
        (
            finance_views
            .finance_student_accounts
        ),
        name="finance-student-accounts",
    ),

    path(
        (
            "finance/accounts/"
            "<uuid:enrollment_id>/"
        ),
        (
            finance_views
            .finance_student_statement
        ),
        name="finance-student-statement",
    ),

    path(
        "finance/debtors/",
        finance_views.finance_debtors,
        name="finance-debtors",
    ),
]