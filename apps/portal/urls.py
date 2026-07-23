from django.urls import path

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
]