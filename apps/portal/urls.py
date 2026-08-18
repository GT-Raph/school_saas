from django.urls import path

from apps.portal import family_views

from . import admin_views, teacher_views, finance_views, academic_views, views, user_views, promotion_views


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


    path(
        "academic/promotions/",
        promotion_views.promotion_dashboard,
        name="promotion-dashboard",
    ),

    path(
        (
            "academic/promotions/"
            "<uuid:policy_id>/run/"
        ),
        promotion_views.promotion_run_policy,
        name="promotion-run-policy",
    ),

    path(
        (
            "academic/promotions/"
            "<uuid:policy_id>/results/"
        ),
        promotion_views.promotion_policy_results,
        name="promotion-policy-results",
    ),

    path(
        (
            "academic/promotions/"
            "evaluation/"
            "<uuid:evaluation_id>/decide/"
        ),
        promotion_views.promotion_decide,
        name="promotion-decide",
    ),

    path(
        (
            "academic/promotions/"
            "decision/"
            "<uuid:decision_id>/execute/"
        ),
        promotion_views.promotion_execute,
        name="promotion-execute",
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

    path(
        "students/import/template/",
        admin_views.student_import_template,
        name="student-import-template",
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

    path(
        "settings/users/",
        user_views.school_user_list,
        name="school-user-list",
    ),

    path(
        "settings/users/create/",
        user_views.school_user_create,
        name="school-user-create",
    ),

    path(
        (
            "settings/users/"
            "<uuid:membership_id>/"
        ),
        user_views.school_user_edit,
        name="school-user-edit",
    ),

     path(
        "academic/results/",
        academic_views.academic_results_queue,
        name="academic-results-queue",
    ),

    path(
        (
            "academic/results/"
            "<uuid:result_id>/approve/"
        ),
        academic_views.academic_approve_result,
        name="academic-approve-result",
    ),

    path(
        "academic/term-results/",
        academic_views.academic_term_results_home,
        name="academic-term-results-home",
    ),

    path(
        (
            "academic/term-results/"
            "<uuid:term_id>/"
            "<uuid:section_id>/"
        ),
        academic_views.academic_term_results,
        name="academic-term-results",
    ),

    path(
        (
            "academic/term-results/"
            "<uuid:term_id>/"
            "<uuid:section_id>/calculate/"
        ),
        (
            academic_views
            .academic_calculate_term_results
        ),
        name="academic-calculate-term-results",
    ),

    path(
        (
            "academic/term-result/"
            "<uuid:term_result_id>/approve/"
        ),
        (
            academic_views
            .academic_approve_term_result
        ),
        name="academic-approve-term-result",
    ),

    path(
        (
            "academic/term-result/"
            "<uuid:term_result_id>/report/"
            "generate/"
        ),
        (
            academic_views
            .academic_generate_report_card
        ),
        name="academic-generate-report-card",
    ),

    path(
        (
            "academic/report-card/"
            "<uuid:report_card_id>/publish/"
        ),
        (
            academic_views
            .academic_publish_report_card
        ),
        name="academic-publish-report-card",
    ),

     path(
        (
            "parent/children/"
            "<uuid:student_id>/"
        ),
        family_views.parent_child_detail,
        name="parent-child-detail",
    ),

    path(
        "student/my-records/",
        family_views.student_self_service,
        name="student-self-service",
    ),

    path(
        (
            "report-cards/"
            "<uuid:report_card_id>/"
        ),
        family_views.family_report_card,
        name="family-report-card",
    ),
]