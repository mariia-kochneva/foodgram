from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from .models import Recipe


class RecipeShortLinkView(APIView):
    """Редирект по короткой ссылке на рецепт."""
    permission_classes = [AllowAny]

    def get(self, request, pk):
        get_object_or_404(Recipe, pk=pk)
        return redirect(reverse('recipe-frontend', kwargs={'pk': pk}))
