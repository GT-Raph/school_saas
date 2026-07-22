from .models import SchoolDomain


class TenantMiddleware:
    """
    Resolves the current tenant from the request hostname.

    Example:
        premier.schoolos.com
            -> Premier Academy
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.school = None

        hostname = (
            request.get_host()
            .split(":")[0]
            .strip()
            .lower()
        )

        domain = (
            SchoolDomain.objects
            .select_related("school")
            .filter(
                domain=hostname,
                is_verified=True,
            )
            .first()
        )

        if domain:
            request.school = domain.school

        return self.get_response(request)