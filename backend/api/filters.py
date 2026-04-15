from django_filters.rest_framework import (
    FilterSet, CharFilter, BooleanFilter, NumberFilter
)

from recipes.models import Recipe, Ingredient


class RecipeFilter(FilterSet):
    """Фильтр для рецептов."""
    author = NumberFilter(field_name='author__id', lookup_expr='exact')
    tags = CharFilter(
        field_name='tags__slug', lookup_expr='exact', method='filter_tags'
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
        """Фильтрация по избранному (только для авторизованных)."""
        user = self.request.user
        if value and user.is_authenticated:
            return queryset.filter(favorites__user=user)
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        """Фильтрация по списку покупок (только для авторизованных)."""
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

    def filter_name(self, queryset, name, value):
        starts_with = queryset.filter(name__istartswith=value)
        contains = (
            queryset
            .filter(name__icontains=value)
            .exclude(name__istartswith=value)
        )
        return starts_with | contains
