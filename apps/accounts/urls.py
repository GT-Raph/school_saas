from django.urls import path

from .views import (
    SchoolLoginView,
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
]