from django.shortcuts import redirect
from django.urls import reverse


class ForcePasswordChangeMiddleware:
    """
    Prevent users with temporary passwords from
    accessing the application until they change them.
    """

    def __init__(
        self,
        get_response,
    ):
        self.get_response = get_response

    def __call__(
        self,
        request,
    ):
        user = getattr(
            request,
            "user",
            None,
        )

        if (
            user
            and user.is_authenticated
            and user.must_change_password
        ):
            password_change_url = reverse(
                "accounts:force-password-change"
            )

            logout_url = reverse(
                "accounts:logout"
            )

            allowed_paths = {
                password_change_url,
                logout_url,
            }

            if (
                request.path
                not in allowed_paths
                and not request.path.startswith(
                    "/static/"
                )
            ):
                return redirect(
                    password_change_url
                )

        return self.get_response(
            request
        )
    