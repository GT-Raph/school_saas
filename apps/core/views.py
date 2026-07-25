import logging

from django.db import connection
from django.http import JsonResponse
from django.views.decorators.cache import (
    never_cache,
)
from django.views.decorators.http import (
    require_GET,
)


logger = logging.getLogger(
    __name__
)


@require_GET
@never_cache
def live_check(
    request,
):
    return JsonResponse(
        {
            "status": "ok",
            "service": "school-saas",
            "request_id": getattr(
                request,
                "request_id",
                None,
            ),
        }
    )


@require_GET
@never_cache
def readiness_check(
    request,
):
    try:

        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT 1"
            )

            cursor.fetchone()

    except Exception:

        logger.exception(
            "Database readiness check failed."
        )

        return JsonResponse(
            {
                "status": "unavailable",
                "database": "unavailable",
                "request_id": getattr(
                    request,
                    "request_id",
                    None,
                ),
            },
            status=503,
        )

    return JsonResponse(
        {
            "status": "ready",
            "database": "available",
            "request_id": getattr(
                request,
                "request_id",
                None,
            ),
        }
    )

def health_check(request):
    return JsonResponse(
        {
            "status": "ok",
            "service": "school-saas",
        }
    )