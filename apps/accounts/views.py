from django.contrib.auth import logout
from django.contrib.auth.views import (
    LoginView,
)
from django.core.exceptions import (
    PermissionDenied,
)
from django.shortcuts import redirect

from apps.schools.models import (
    SchoolMembership,
)

from .forms import (
    SchoolAuthenticationForm,
)


class SchoolLoginView(LoginView):

    template_name = (
        "accounts/login.html"
    )

    authentication_form = (
        SchoolAuthenticationForm
    )

    redirect_authenticated_user = (
        True
    )

    def form_valid(
        self,
        form,
    ):
        user = form.get_user()

        school = getattr(
            self.request,
            "school",
            None,
        )

        if not school:

            form.add_error(
                None,
                (
                    "This school portal "
                    "could not be identified."
                ),
            )

            return self.form_invalid(
                form
            )

        if (
            not user.is_superuser
            and not user.is_platform_admin
        ):

            membership_exists = (
                SchoolMembership.objects
                .filter(
                    user=user,
                    school=school,
                    is_active=True,
                )
                .exists()
            )

            if not membership_exists:

                form.add_error(
                    None,
                    (
                        "Your account does "
                        "not have access to "
                        "this school."
                    ),
                )

                return self.form_invalid(
                    form
                )

        return super().form_valid(
            form
        )

    def get_success_url(
        self,
    ):
        return "/portal/"


def school_logout(
    request,
):
    logout(request)

    return redirect(
        "accounts:login"
    )