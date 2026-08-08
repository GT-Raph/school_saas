from django.urls import path

from . import views


app_name = "accounts"


urlpatterns = [
    path(
        "login/",
        views.central_login,
        name="login",
    ),

    path(
        "post-login/",
        views.post_login,
        name="post-login",
    ),

    path(
        "choose-school/",
        views.choose_school,
        name="choose-school",
    ),

    path(
        "handoff/",
        views.tenant_handoff,
        name="handoff",
    ),

    path(
        "change-temporary-password/",
        views.force_password_change,
        name="force-password-change",
    ),

    path(
        "logout/",
        views.school_logout,
        name="logout",
    ),
]