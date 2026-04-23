from rest_framework import permissions


class IsAuthorOrReadOnly(permissions.BasePermission):
    """Права доступа для рецептов."""

    def has_object_permission(self, request, view, obj):
        return (
            request.method in permissions.SAFE_METHODS
            or obj.author == request.user
        )


class IsAuthenticatedOnly(permissions.BasePermission):
    """Права доступа для избранного, списка покупок и подписок."""

    def has_permission(self, request, view):
        return request.user.is_authenticated