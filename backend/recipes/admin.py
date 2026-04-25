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
    """Базовый класс для избранного, покупок и подписок."""
    list_display = ('id', 'user_email', 'recipe_info')
    search_fields = ('user__username', 'user__email', 'recipe__name')
    raw_id_fields = ('user', 'recipe')
    ordering = ('-id',)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'user', 'recipe__author'
        )

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'Email пользователя'
    user_email.admin_order_field = 'user__email'

    def recipe_info(self, obj):
        return f'{obj.recipe.name} (автор: {obj.recipe.author.username})'
    recipe_info.short_description = 'Рецепт'


@admin.register(Favorite)
class FavoriteAdmin(BaseUserRecipeAdmin):
    pass


@admin.register(ShoppingCart)
class ShoppingCartAdmin(BaseUserRecipeAdmin):
    pass


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


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('id', 'subscriber_email', 'author_email', 'created')
    search_fields = (
        'user__email', 'user__username', 'author__email', 'author__username'
    )
    raw_id_fields = ('user', 'author')
    ordering = ('-created',)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'author')

    def subscriber_email(self, obj):
        return obj.user.email
    subscriber_email.short_description = 'Подписчик'
    subscriber_email.admin_order_field = 'user__email'

    def author_email(self, obj):
        return obj.author.email
    author_email.short_description = 'Автор'
    author_email.admin_order_field = 'author__email'


admin.site.unregister(Group)
