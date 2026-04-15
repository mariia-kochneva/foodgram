from rest_framework import permissions


class IsAuthorOrReadOnly(permissions.BasePermission):
    """Права доступа для рецептов."""

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.author == request.user


class IsAuthenticatedOnly(permissions.BasePermission):
    """Права доступа для избранного, списка покупок и подписок."""

    def has_permission(self, request, view):
        return request.user.is_authenticated
