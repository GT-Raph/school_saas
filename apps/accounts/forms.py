from django.contrib.auth.forms import (
    AuthenticationForm,
)


class SchoolAuthenticationForm(
    AuthenticationForm
):
    """
    Normal Django authentication,
    with school membership validated
    in the login view.
    """

    pass