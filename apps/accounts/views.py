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

from django.conf import settings

from django.contrib import (
    messages,
)

from django.contrib.auth import (
    login,
    logout,
)

from django.contrib.auth.forms import (
    AuthenticationForm,
)

from django.contrib.auth.decorators import (
    login_required,
)

from django.core.exceptions import (
    ValidationError,
)

from django.http import (
    HttpResponseBadRequest,
)

from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)

from django.views.decorators.csrf import (
    csrf_exempt,
)

from django.views.decorators.http import (
    require_POST,
)

from apps.schools.models import (
    SchoolMembership,
)

from .handoff import (
    consume_login_handoff,
    create_login_handoff,
)

from .platform_urls import (
    platform_url,
    school_url,
)


def get_active_memberships(
    user,
):
    return (
        SchoolMembership.objects
        .filter(
            user=user,
            is_active=True,
        )
        .select_related(
            "school"
        )
        .prefetch_related(
            "roles"
        )
        .order_by(
            "school__name"
        )
    )


def render_handoff(
    request,
    *,
    membership,
):
    token = create_login_handoff(
        user=request.user,
        school=membership.school,
    )

    target_url = school_url(
        school=membership.school,
        path="/accounts/handoff/",
    )

    return render(
        request,
        (
            "accounts/"
            "login_handoff.html"
        ),
        {
            "school":
                membership.school,

            "target_url":
                target_url,

            "token":
                token,
        },
    )


def central_login(
    request,
):
    """
    Platform-wide login.

    Users do not need to know their school's URL.
    """

    # If somebody visits a school's /accounts/login/,
    # send them to the central login page.
    if getattr(
        request,
        "school",
        None,
    ):

        return redirect(
            platform_url(
                "/accounts/login/"
            )
        )

    if request.user.is_authenticated:

        return redirect(
            "accounts:post-login"
        )

    if request.method == "POST":

        form = AuthenticationForm(
            request=request,
            data=request.POST,
        )

        if form.is_valid():

            user = form.get_user()

            login(
                request,
                user,
            )

            return redirect(
                "accounts:post-login"
            )

    else:

        form = AuthenticationForm(
            request=request
        )

    return render(
        request,
        (
            "accounts/"
            "central_login.html"
        ),
        {
            "form": form,
        },
    )


@login_required
def post_login(
    request,
):
    memberships = list(
        get_active_memberships(
            request.user
        )
    )

    if not memberships:

        return render(
            request,
            (
                "accounts/"
                "no_school_access.html"
            ),
        )

    if len(memberships) == 1:

        return render_handoff(
            request,
            membership=(
                memberships[0]
            ),
        )

    return redirect(
        "accounts:choose-school"
    )


@login_required
def choose_school(
    request,
):
    memberships = (
        get_active_memberships(
            request.user
        )
    )

    if request.method == "POST":

        membership = get_object_or_404(
            memberships,
            id=request.POST.get(
                "membership_id"
            ),
        )

        return render_handoff(
            request,
            membership=membership,
        )

    return render(
        request,
        (
            "accounts/"
            "choose_school.html"
        ),
        {
            "memberships":
                memberships,
        },
    )


@csrf_exempt
@require_POST
def tenant_handoff(
    request,
):
    """
    Consume a short-lived handoff credential and
    establish a session on the destination school host.

    This endpoint is intentionally CSRF-exempt because
    authentication depends on a cryptographically random,
    one-use, short-lived credential rather than an
    existing browser session.
    """

    school = getattr(
        request,
        "school",
        None,
    )

    if not school:

        return HttpResponseBadRequest(
            "School could not be identified."
        )

    try:

        user = consume_login_handoff(
            token=request.POST.get(
                "token",
                "",
            ),

            school=school,
        )

    except ValidationError as exc:

        return render(
            request,
            (
                "accounts/"
                "handoff_error.html"
            ),
            {
                "errors":
                    exc.messages,
            },
            status=400,
        )

    backend = (
        settings
        .AUTHENTICATION_BACKENDS[0]
    )

    login(
        request,
        user,
        backend=backend,
    )

    if user.must_change_password:

        return redirect(
            (
                "accounts:"
                "force-password-change"
            )
        )

    return redirect(
        "portal:home"
    )


def school_logout(
    request,
):
    logout(
        request
    )

    return redirect(
        platform_url(
            "/accounts/login/"
        )
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

            if getattr(
                request,
                "school",
                None,
            ):

                return redirect(
                    "portal:home"
                )


            return redirect(
                "accounts:post-login"
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