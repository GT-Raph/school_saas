from functools import wraps

from django.core.exceptions import (
    PermissionDenied,
)

from apps.accounts.decorators import (
    tenant_login_required,
)

from .models import SchoolSubscription


def subscription_write_required(
    view_func,
):
    @wraps(view_func)
    @tenant_login_required
    def wrapper(
        request,
        *args,
        **kwargs,
    ):
        try:
            subscription = (
                request.school.subscription
            )

        except (
            SchoolSubscription.DoesNotExist
        ):
            raise PermissionDenied(
                "No active subscription "
                "is configured."
            )

        if not subscription.can_write:

            raise PermissionDenied(
                (
                    "This school's subscription "
                    "is currently read-only or "
                    "suspended."
                )
            )

        return view_func(
            request,
            *args,
            **kwargs,
        )

    return wrapper