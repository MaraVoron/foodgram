from rest_framework import permissions
from rest_framework.permissions import IsAuthenticatedOrReadOnly


class IsAuthorOrReadOnly(IsAuthenticatedOrReadOnly):
    """Класс для прав доступа."""

    def has_object_permission(self, request, view, obj):
        """Проверка прав доступа."""
        return (
            request.method in permissions.SAFE_METHODS or
            obj.author == request.user
        )
