from django.contrib import admin
from django.urls import path, include

from recipes.views import RecipeShortLinkView


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    path(
        'r/<int:pk>/', RecipeShortLinkView.as_view(), name='recipe-short-link'
    ),
    path(
        'recipes/<int:pk>/', RecipeShortLinkView.as_view(),
        name='recipe-frontend'
    ),
]
