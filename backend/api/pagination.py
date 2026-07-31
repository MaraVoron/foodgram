from rest_framework.pagination import PageNumberPagination

from recipes.constants import DEFAULT_PAGE_SIZE


class LimitPagination(PageNumberPagination):
    """Пагинация с поддержкой параметра limit."""

    page_size_query_param = 'limit'
    page_size = DEFAULT_PAGE_SIZE
