from functools import wraps

from django.conf import settings
from django.contrib.auth.views import (
    redirect_to_login,
)
from django.core.exceptions import (
    PermissionDenied,
)
from django.shortcuts import redirect

from apps.schools.permissions import (
    has_school_permission,
)


def tenant_login_required(
    view_func,
):
    @wraps(view_func)
    def wrapper(
        request,
        *args,
        **kwargs,
    ):
        if not request.user.is_authenticated:

            return redirect_to_login(
                request.get_full_path(),
                settings.LOGIN_URL,
            )

        if not request.school:

            raise PermissionDenied(
                "No school tenant "
                "was resolved."
            )

        if (
            request.user.is_superuser
            or request.user
            .is_platform_admin
        ):
            return view_func(
                request,
                *args,
                **kwargs,
            )

        if not request.active_membership:

            raise PermissionDenied(
                "You do not have access "
                "to this school."
            )

        return view_func(
            request,
            *args,
            **kwargs,
        )

    return wrapper


def school_permission_required(
    permission,
):
    def decorator(
        view_func,
    ):
        @wraps(view_func)
        @tenant_login_required
        def wrapper(
            request,
            *args,
            **kwargs,
        ):
            allowed = (
                has_school_permission(
                    user=request.user,
                    school=request.school,
                    permission=permission,
                )
            )

            if not allowed:
                raise PermissionDenied(
                    "You do not have "
                    "permission to perform "
                    "this action."
                )

            return view_func(
                request,
                *args,
                **kwargs,
            )

        return wrapper

    return decorator