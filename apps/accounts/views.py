from django.conf import settings

from django.contrib import messages

from django.contrib.auth import (
    login,
    logout,
    update_session_auth_hash,
)

from django.contrib.auth.decorators import (
    login_required,
)

from django.contrib.auth.forms import (
    AuthenticationForm,
    PasswordChangeForm,
)

from django.contrib.auth.views import (
    LoginView,
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


from .forms import (
    SchoolAuthenticationForm,
)

from .handoff import (
    consume_login_handoff,
    create_login_handoff,
)

from .platform_urls import (
    platform_url,
    school_url,
)


# ============================================================
# MEMBERSHIP HELPERS
# ============================================================


def get_active_memberships(
    user,
):
    """
    Return all active school memberships for a user.

    Used by the central login flow to determine which
    school or schools the authenticated user can access.
    """

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


# ============================================================
# LOGIN HANDOFF CREATION
# ============================================================


def render_handoff(
    request,
    *,
    membership,
):
    """
    Create a short-lived, one-use login handoff token.

    The user's central-login session is destroyed after
    the token has been created.

    The destination school host establishes a completely
    separate authenticated session when the handoff token
    is consumed.
    """

    school = (
        membership.school
    )

    # --------------------------------------------------------
    # Create handoff while central session is authenticated.
    # --------------------------------------------------------

    token = (
        create_login_handoff(
            user=request.user,
            school=school,
        )
    )

    target_url = (
        school_url(
            school=school,
            path="/accounts/handoff/",
        )
    )

    # --------------------------------------------------------
    # IMPORTANT
    #
    # Destroy the central session BEFORE sending the browser
    # to the tenant.
    #
    # Otherwise:
    #
    # tenant logout
    #     -> login.localhost
    #     -> central session still authenticated
    #     -> automatic handoff
    #     -> user appears logged in again
    # --------------------------------------------------------

    logout(
        request
    )

    return render(
        request,
        "accounts/login_handoff.html",
        {
            "school":
                school,

            "target_url":
                target_url,

            "token":
                token,
        },
    )


# ============================================================
# CENTRAL LOGIN
# ============================================================


def central_login(
    request,
):
    """
    Main platform login.

    Development:
        login.localhost:8000

    Production:
        login.<platform-domain>

    Users should not need to know a school's tenant URL
    before signing in.
    """

    # --------------------------------------------------------
    # If somebody opens /accounts/login/ on a school host,
    # send them to central login.
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # Already authenticated centrally
    # --------------------------------------------------------

    if (
        request.user
        .is_authenticated
    ):

        return redirect(
            "accounts:post-login"
        )

    # --------------------------------------------------------
    # Login submission
    # --------------------------------------------------------

    if (
        request.method
        == "POST"
    ):

        form = (
            AuthenticationForm(
                request=request,
                data=request.POST,
            )
        )

        if form.is_valid():

            user = (
                form.get_user()
            )

            login(
                request,
                user,
            )

            return redirect(
                "accounts:post-login"
            )

    else:

        form = (
            AuthenticationForm(
                request=request
            )
        )

    return render(
        request,
        "accounts/central_login.html",
        {
            "form":
                form,
        },
    )


# ============================================================
# CENTRAL POST LOGIN
# ============================================================


@login_required
def post_login(
    request,
):
    """
    Determine which school the user should enter.

    0 memberships:
        show no-school-access page

    1 membership:
        automatically create handoff

    2+ memberships:
        let user choose school
    """

    memberships = list(
        get_active_memberships(
            request.user
        )
    )

    if not memberships:

        return render(
            request,
            "accounts/no_school_access.html",
        )

    if (
        len(
            memberships
        )
        == 1
    ):

        return render_handoff(
            request,
            membership=(
                memberships[0]
            ),
        )

    return redirect(
        "accounts:choose-school"
    )


# ============================================================
# CHOOSE SCHOOL
# ============================================================


@login_required
def choose_school(
    request,
):
    """
    Allow users with multiple memberships to select the
    school they want to enter.
    """

    memberships = (
        get_active_memberships(
            request.user
        )
    )

    if (
        request.method
        == "POST"
    ):

        membership = (
            get_object_or_404(
                memberships,
                id=(
                    request.POST.get(
                        "membership_id"
                    )
                ),
            )
        )

        return render_handoff(
            request,
            membership=membership,
        )

    return render(
        request,
        "accounts/choose_school.html",
        {
            "memberships":
                memberships,
        },
    )


# ============================================================
# TENANT HANDOFF
# ============================================================


@csrf_exempt
@require_POST
def tenant_handoff(
    request,
):
    """
    Consume a one-use handoff credential on the destination
    tenant host and establish the tenant's Django session.

    CSRF exemption is intentional here because authentication
    is based on the short-lived cryptographically random
    handoff credential itself.
    """

    school = getattr(
        request,
        "school",
        None,
    )

    if not school:

        return HttpResponseBadRequest(
            (
                "School could not "
                "be identified."
            )
        )

    token = (
        request.POST.get(
            "token",
            ""
        )
    )

    if not token:

        return render(
            request,
            "accounts/handoff_error.html",
            {
                "error":
                    (
                        "Login token was "
                        "not provided."
                    ),

                "central_login_url":
                    platform_url(
                        "/accounts/login/"
                    ),
            },
            status=400,
        )

    try:

        user = (
            consume_login_handoff(
                token=token,
                school=school,
            )
        )

    except ValidationError as exc:

        error_message = (
            exc.messages[0]
            if exc.messages
            else (
                "The login request "
                "could not be completed."
            )
        )

        return render(
            request,
            "accounts/handoff_error.html",
            {
                "error":
                    error_message,

                "central_login_url":
                    platform_url(
                        "/accounts/login/"
                    ),
            },
            status=400,
        )

    # --------------------------------------------------------
    # Explicit backend is necessary because this user was not
    # authenticated through authenticate() on this host.
    # --------------------------------------------------------

    backend = (
        settings
        .AUTHENTICATION_BACKENDS[0]
    )

    login(
        request,
        user,
        backend=backend,
    )

    # --------------------------------------------------------
    # Temporary-password workflow
    # --------------------------------------------------------

    if getattr(
        user,
        "must_change_password",
        False,
    ):

        return redirect(
            "accounts:force-password-change"
        )

    return redirect(
        "portal:home"
    )


# ============================================================
# SCHOOL LOGOUT
# ============================================================


def school_logout(
    request,
):
    """
    Destroy the tenant-host session and return the user to
    the CENTRAL login host.

    Do not redirect using "accounts:login" here because that
    creates a relative /accounts/login/ URL on the current
    tenant hostname.
    """

    logout(
        request
    )

    return redirect(
        platform_url(
            "/accounts/login/"
        )
    )


# ============================================================
# LEGACY SCHOOL LOGIN VIEW
# ============================================================


class SchoolLoginView(
    LoginView
):
    """
    Legacy school-host login view.

    The standard architecture now uses central_login() and
    login handoff. This class is retained only in case an
    existing URL or test still imports it.
    """

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
        user = (
            form.get_user()
        )

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

            return (
                self.form_invalid(
                    form
                )
            )

        is_platform_admin = (
            getattr(
                user,
                "is_platform_admin",
                False,
            )
        )

        if (
            not user.is_superuser
            and not is_platform_admin
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

                return (
                    self.form_invalid(
                        form
                    )
                )

        return super().form_valid(
            form
        )

    def get_success_url(
        self,
    ):
        return "/portal/"


# ============================================================
# FORCED PASSWORD CHANGE
# ============================================================


@login_required
def force_password_change(
    request,
):
    """
    Require users with temporary passwords to choose a new
    password before continuing into the portal.
    """

    if (
        request.method
        == "POST"
    ):

        form = (
            PasswordChangeForm(
                user=request.user,
                data=request.POST,
            )
        )

        if form.is_valid():

            user = (
                form.save()
            )

            if hasattr(
                user,
                "must_change_password",
            ):

                user.must_change_password = (
                    False
                )

                user.save(
                    update_fields=[
                        (
                            "must_change_password"
                        ),
                        "updated_at",
                    ]
                )

            # Keep the current session valid after password
            # change.
            update_session_auth_hash(
                request,
                user,
            )

            messages.success(
                request,
                (
                    "Your password was "
                    "changed successfully."
                ),
            )

            # -----------------------------------------------
            # Password changed while on tenant host.
            # -----------------------------------------------

            if getattr(
                request,
                "school",
                None,
            ):

                return redirect(
                    "portal:home"
                )

            # -----------------------------------------------
            # Password changed on central host.
            # -----------------------------------------------

            return redirect(
                "accounts:post-login"
            )

    else:

        form = (
            PasswordChangeForm(
                user=request.user
            )
        )

    return render(
        request,
        (
            "accounts/"
            "force_password_change.html"
        ),
        {
            "form":
                form,
        },
    )