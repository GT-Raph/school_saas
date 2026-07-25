import logging
import re
import uuid
from contextvars import ContextVar


request_id_context = ContextVar(
    "request_id",
    default="-",
)


REQUEST_ID_PATTERN = re.compile(
    r"^[A-Za-z0-9._-]{8,100}$"
)


class RequestIDMiddleware:
    """
    Add a unique request ID to every request and response.

    A valid X-Request-ID supplied by Render or another
    proxy may be preserved.
    """

    def __init__(
        self,
        get_response,
    ):
        self.get_response = get_response

    def __call__(
        self,
        request,
    ):
        supplied_request_id = (
            request.headers.get(
                "X-Request-ID",
                "",
            )
        )

        if REQUEST_ID_PATTERN.fullmatch(
            supplied_request_id
        ):
            request_id = (
                supplied_request_id
            )

        else:
            request_id = (
                uuid.uuid4().hex
            )

        token = request_id_context.set(
            request_id
        )

        request.request_id = request_id

        try:
            response = self.get_response(
                request
            )

            response[
                "X-Request-ID"
            ] = request_id

            return response

        finally:
            request_id_context.reset(
                token
            )


class RequestIDFilter(
    logging.Filter
):
    """
    Add the current request ID to log records.
    """

    def filter(
        self,
        record,
    ):
        record.request_id = (
            request_id_context.get()
        )

        return True