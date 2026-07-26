from rest_framework import permissions


class IsAuthorOrReadOnly(permissions.BasePermission):
    """
    Права доступа: чтение для всех, запись только для авторов.

    Чтение доступно всем пользователям.
    Создание доступно только авторизованным.
    Редактирование и удаление доступно только автору объекта.
    """

    def has_permission(self, request, view):
        """Проверка прав на уровне запроса."""
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        """Проверка прав на уровне объекта."""
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.author == request.user
