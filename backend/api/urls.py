from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    TagViewSet,
    IngredientViewSet,
    RecipeViewSet,
    UserViewSet,
    RegisterView,
)
from .views import RecipeShortLinkView


router = DefaultRouter()
router.register('tags', TagViewSet, basename='tags')
router.register('ingredients', IngredientViewSet, basename='ingredients')
router.register('recipes', RecipeViewSet, basename='recipes')
router.register('users', UserViewSet, basename='users')

urlpatterns = [
    path('', include(router.urls)),
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
    path(
        'r/<int:pk>/', RecipeShortLinkView.as_view(), name='recipe-short-link'
    ),
]
