from django.conf import settings

from .models import (
    School,
    SchoolDomain,
    SchoolMembership,
)


class TenantMiddleware:
    """
    Resolve the active school/tenant.

    Production:
        premier.yourplatform.com

    Development fallback:
        DEV_TENANT_SLUG=demo-international-school
    """

    def __init__(
        self,
        get_response,
    ):
        self.get_response = (
            get_response
        )

    def __call__(
        self,
        request,
    ):
        request.school = None
        request.active_membership = None

        hostname = (
            request.get_host()
            .split(":")[0]
            .strip()
            .lower()
        )

        domain = (
            SchoolDomain.objects
            .select_related(
                "school"
            )
            .filter(
                domain=hostname,
                is_verified=True,
            )
            .first()
        )

        if domain:
            request.school = (
                domain.school
            )

        elif settings.DEBUG:

            dev_tenant_slug = getattr(
                settings,
                "DEV_TENANT_SLUG",
                "",
            )

            if dev_tenant_slug:
                request.school = (
                    School.objects
                    .filter(
                        slug=(
                            dev_tenant_slug
                        )
                    )
                    .first()
                )

        if (
            request.school
            and request.user
            .is_authenticated
        ):
            request.active_membership = (
                SchoolMembership.objects
                .filter(
                    school=request.school,
                    user=request.user,
                    is_active=True,
                )
                .prefetch_related(
                    "roles"
                )
                .first()
            )

        return self.get_response(
            request
        )