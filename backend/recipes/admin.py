from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group
from django.db.models import Count

from users.models import User, Subscription
from .constants import SHORT_TEXT_LENGTH
from .models import (
    Favorite, Ingredient, Recipe, RecipeIngredient, ShoppingCart, Tag
)


class ShortTextMixin:
    """Миксин для обрезки длинного текста."""

    def short_text(self, obj):
        return (
            obj.text[:SHORT_TEXT_LENGTH] + '…'
            if len(obj.text) > SHORT_TEXT_LENGTH
            else obj.text
        )
    short_text.short_description = 'Описание'


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'slug')
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('name',)


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'measurement_unit')
    search_fields = ('name',)
    list_filter = ('measurement_unit',)
    ordering = ('name',)


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 1
    min_num = 1
    verbose_name = 'Ингредиент'
    verbose_name_plural = 'Ингредиенты'


@admin.register(Recipe)
class RecipeAdmin(ShortTextMixin, admin.ModelAdmin):
    list_display = (
        'id', 'name', 'author', 'cooking_time',
        'display_tags', 'favorite_count', 'pub_date', 'short_text'
    )
    list_filter = ('tags', 'pub_date')
    search_fields = ('name', 'author__username', 'author__email', 'text')
    filter_horizontal = ('tags',)
    inlines = [RecipeIngredientInline]
    readonly_fields = ('favorite_count', 'pub_date')
    ordering = ('-pub_date',)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'author'
        ).prefetch_related(
            'tags'
        ).annotate(
            fav_count=Count('favorites', distinct=True)
        )

    def display_tags(self, obj):
        tag_names = obj.tags.values_list('name', flat=True)
        return ', '.join(tag_names) if tag_names else '—'
    display_tags.short_description = 'Теги'

    def favorite_count(self, obj):
        if hasattr(obj, 'fav_count'):
            return obj.fav_count
        return obj.favorites.count()
    favorite_count.short_description = 'В избранном'
    favorite_count.admin_order_field = 'fav_count'


class BaseUserRecipeAdmin(admin.ModelAdmin):
    """Базовый класс для избранного и списка покупок."""
    list_display = ('id', 'favorite_info', 'author_info')
    list_filter = ('recipe__tags',)
    search_fields = ('user__username', 'user__email', 'recipe__name')
    raw_id_fields = ('user', 'recipe')
    ordering = ('-id',)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'user', 'recipe__author'
        ).prefetch_related('recipe__tags')

    def favorite_info(self, obj):
        return f'{obj.user.email} — "{obj.recipe.name}"'
    favorite_info.short_description = 'Избранное/Покупки'

    def author_info(self, obj):
        return obj.recipe.author.username
    author_info.short_description = 'Автор рецепта'


@admin.register(Favorite)
class FavoriteAdmin(BaseUserRecipeAdmin):
    pass


@admin.register(ShoppingCart)
class ShoppingCartAdmin(BaseUserRecipeAdmin):
    pass


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    """Подписки."""
    list_display = ('id', 'subscription_info', 'created')
    list_filter = ('created',)
    search_fields = (
        'user__email', 'user__username', 'author__email', 'author__username'
    )
    raw_id_fields = ('user', 'author')
    ordering = ('-created',)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'author')

    def subscription_info(self, obj):
        return f'{obj.user.email} подписан на {obj.author.email}'
    subscription_info.short_description = 'Подписка'


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """Пользователи."""
    list_display = (
        'id', 'username', 'email', 'first_name', 'last_name',
        'is_active', 'is_staff', 'date_joined'
    )
    list_filter = ('is_active', 'is_staff', 'is_superuser', 'date_joined')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('-date_joined',)

    fieldsets = (
        ('Основное', {
            'fields': ('email', 'username', 'password')
        }),
        ('Личная информация', {
            'fields': ('first_name', 'last_name', 'avatar')
        }),
        ('Права', {
            'fields': (
                'is_active', 'is_staff', 'is_superuser',
                'groups', 'user_permissions'
            )
        }),
        ('Даты', {
            'fields': ('last_login', 'date_joined')
        }),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'email', 'username', 'first_name', 'last_name',
                'password1', 'password2'
            ),
        }),
    )


admin.site.unregister(Group)
