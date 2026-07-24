from django.urls import path

from .views import (
    SchoolLoginView,
    force_password_change,
    school_logout,
)


app_name = "accounts"


urlpatterns = [
    path(
        "login/",
        SchoolLoginView.as_view(),
        name="login",
    ),

    path(
        "logout/",
        school_logout,
        name="logout",
    ),

    path(
        "change-temporary-password/",
        force_password_change,
        name="force-password-change",
    ),
]