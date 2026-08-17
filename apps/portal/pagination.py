from django.core.paginator import Paginator


DEFAULT_PAGE_SIZE = 15


def paginate(
    request,
    items,
    *,
    per_page=DEFAULT_PAGE_SIZE,
    page_param="page",
):
    paginator = Paginator(
        items,
        per_page,
    )

    page_obj = paginator.get_page(
        request.GET.get(
            page_param
        )
    )

    # Preserve search/filter parameters
    # when moving between pages.
    query_params = (
        request.GET.copy()
    )

    query_params.pop(
        page_param,
        None,
    )

    return (
        page_obj,
        query_params.urlencode(),
    )