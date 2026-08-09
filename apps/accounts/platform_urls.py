from django.conf import settings
from django.core.exceptions import (
    ImproperlyConfigured,
)


def platform_origin():
    if settings.DEBUG:

        port = (
            settings.DEV_SERVER_PORT
        )

        origin = (
            "http://"
            + settings
            .PLATFORM_LOGIN_HOST
        )

        if port:
            origin += (
                ":"
                + port
            )

        return origin

    if not settings.PLATFORM_LOGIN_HOST:

        raise ImproperlyConfigured(
            (
                "PLATFORM_LOGIN_HOST "
                "is required."
            )
        )

    return (
        "https://"
        + settings
        .PLATFORM_LOGIN_HOST
    )


def platform_url(
    path="/",
):
    return (
        platform_origin()
        + "/"
        + path.lstrip("/")
    )


def school_origin(
    school,
):
    if settings.DEBUG:

        host = (
            f"{school.slug}"
            ".localhost"
        )

        origin = (
            "http://"
            + host
        )

        if settings.DEV_SERVER_PORT:

            origin += (
                ":"
                + settings
                .DEV_SERVER_PORT
            )

        return origin

    if not settings.PLATFORM_BASE_DOMAIN:

        raise ImproperlyConfigured(
            (
                "PLATFORM_BASE_DOMAIN "
                "must be configured "
                "in production."
            )
        )

    return (
        f"https://"
        f"{school.slug}."
        f"{settings.PLATFORM_BASE_DOMAIN}"
    )


def school_url(
    *,
    school,
    path="/",
):
    return (
        school_origin(
            school
        )
        + "/"
        + path.lstrip("/")
    )