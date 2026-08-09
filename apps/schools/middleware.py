from django.conf import settings

from .models import (
    School,
    SchoolDomain,
    SchoolMembership,
)


class TenantMiddleware:
    """
    Resolve a tenant from the request hostname.

    Development:
        stanne.localhost
        demo.localhost

    Production:
        stanne.example.com
        demo.example.com

    Optional custom domains:
        portal.some-school.edu.gh

    Platform hosts such as login.example.com
    do not resolve to a school.
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

        request.active_membership = (
            None
        )

        hostname = (
            request.get_host()
            .split(":")[0]
            .strip()
            .lower()
        )

        platform_hosts = {
            "localhost",
            "127.0.0.1",
            settings.PLATFORM_LOGIN_HOST,
        }

        if settings.PLATFORM_BASE_DOMAIN:

            platform_hosts.update(
                {
                    settings
                    .PLATFORM_BASE_DOMAIN,

                    (
                        "www."
                        + settings
                        .PLATFORM_BASE_DOMAIN
                    ),
                }
            )

        # -----------------------------------------------------------
        # Central/platform host
        # -----------------------------------------------------------

        if hostname in platform_hosts:

            request.school = None

        else:

            # -------------------------------------------------------
            # Explicit custom domain
            # -------------------------------------------------------

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

            # -------------------------------------------------------
            # Development subdomain
            # -------------------------------------------------------

            elif (
                settings.DEBUG
                and hostname.endswith(
                    ".localhost"
                )
            ):

                slug = hostname[
                    :-len(".localhost")
                ]

                if (
                    slug
                    and slug
                    not in settings
                    .PLATFORM_RESERVED_SUBDOMAINS
                ):

                    request.school = (
                        School.objects
                        .filter(
                            slug=slug
                        )
                        .first()
                    )

            # -------------------------------------------------------
            # Production SaaS subdomain
            # -------------------------------------------------------

            elif (
                settings
                .PLATFORM_BASE_DOMAIN

                and hostname.endswith(
                    "."
                    + settings
                    .PLATFORM_BASE_DOMAIN
                )
            ):

                suffix = (
                    "."
                    + settings
                    .PLATFORM_BASE_DOMAIN
                )

                slug = hostname[
                    :-len(suffix)
                ]

                # Only standard single-label
                # subdomains are considered.
                if (
                    slug
                    and "." not in slug
                    and slug
                    not in settings
                    .PLATFORM_RESERVED_SUBDOMAINS
                ):

                    request.school = (
                        School.objects
                        .filter(
                            slug=slug
                        )
                        .first()
                    )

        # -----------------------------------------------------------
        # Current user's membership for this tenant
        # -----------------------------------------------------------

        if (
            request.school
            and request.user.is_authenticated
        ):

            request.active_membership = (
                SchoolMembership.objects
                .filter(
                    school=(
                        request.school
                    ),

                    user=(
                        request.user
                    ),

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