from django.contrib.auth import (
    logout, update_session_auth_hash,
    )
from django.contrib.auth.views import (
    LoginView,
)
from django.core.exceptions import (
    PermissionDenied,
)

from django.contrib.auth.forms import (
    PasswordChangeForm,
)

from django.contrib.auth.decorators import (
    login_required,
)

from django.contrib import messages
from django.shortcuts import render

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

@login_required
def force_password_change(
    request,
):
    if request.method == "POST":

        form = PasswordChangeForm(
            user=request.user,
            data=request.POST,
        )

        if form.is_valid():

            user = form.save()

            user.must_change_password = False

            user.save(
                update_fields=[
                    "must_change_password",
                    "updated_at",
                ]
            )

            update_session_auth_hash(
                request,
                user,
            )

            messages.success(
                request,
                (
                    "Your password was changed "
                    "successfully."
                ),
            )

            return redirect(
                "/portal/"
            )

    else:

        form = PasswordChangeForm(
            user=request.user
        )

    return render(
        request,
        "accounts/force_password_change.html",
        {
            "form": form,
        },
    )