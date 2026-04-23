from django_filters.rest_framework import (
    BooleanFilter, CharFilter, FilterSet
)

from recipes.models import Ingredient, Recipe


class RecipeFilter(FilterSet):
    """Фильтр для рецептов."""
    tags = CharFilter(
        field_name='tags__slug', method='filter_tags'
    )
    is_favorited = BooleanFilter(method='filter_is_favorited')
    is_in_shopping_cart = BooleanFilter(method='filter_is_in_shopping_cart')

    class Meta:
        model = Recipe
        fields = ['author', 'tags', 'is_favorited', 'is_in_shopping_cart']

    def filter_tags(self, queryset, name, value):
        """Фильтрация по нескольким тегам (slug)."""
        tags_slugs = self.request.GET.getlist('tags')
        if tags_slugs:
            return queryset.filter(tags__slug__in=tags_slugs).distinct()
        return queryset

    def filter_is_favorited(self, queryset, name, value):
        user = self.request.user
        if value and user.is_authenticated:
            return queryset.filter(favorites__user=user)
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        user = self.request.user
        if value and user.is_authenticated:
            return queryset.filter(shopping_cart__user=user)
        return queryset


class IngredientFilter(FilterSet):
    """Фильтр для ингредиентов."""
    name = CharFilter(field_name='name', lookup_expr='istartswith')

    class Meta:
        model = Ingredient
        fields = ['name']
