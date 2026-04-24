import re

from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from recipes.models import Ingredient, Recipe, RecipeIngredient, Tag
from users.models import User


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для тегов."""

    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для ингредиентов."""

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class RecipeIngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для ингредиентов в рецепте."""

    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all()
    )
    name = serializers.CharField(source='ingredient.name', read_only=True)
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit',
        read_only=True
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Сериализатор для регистрации пользователя."""

    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ('email', 'username', 'first_name', 'last_name', 'password')

    def validate_username(self, value):
        if value.lower() == 'me':
            raise ValidationError('Имя пользователя "me" запрещено')
        if not re.match(r'^[\w.@+-]+$', value):
            raise ValidationError(
                'Username может содержать только буквы,'
                ' цифры и символы @/./+/-/_'
            )
        return value

    def validate_email(self, value):
        return value.strip().lower()

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User.objects.create_user(**validated_data, password=password)
        return user


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор для пользователей."""

    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name',
            'last_name', 'avatar', 'is_subscribed'
        )

    def get_is_subscribed(self, obj):
        """Проверка подписки текущего пользователя."""
        request = self.context.get('request')
        return (request and request.user.is_authenticated
                and obj.following.filter(user=request.user).exists())


class RecipeListSerializer(serializers.ModelSerializer):
    """Сериализатор для списка рецептов."""

    author = UserSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    ingredients = RecipeIngredientSerializer(
        source='recipe_ingredients', many=True, read_only=True
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients',
            'is_favorited', 'is_in_shopping_cart',
            'name', 'image', 'text', 'cooking_time'
        )

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        return (request and request.user.is_authenticated
                and obj.favorites.filter(user=request.user).exists())

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        return (request and request.user.is_authenticated
                and obj.shopping_cart.filter(user=request.user).exists())


class RecipeIngredientCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания ингредиентов в рецепте."""

    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())
    amount = serializers.IntegerField(min_value=1)

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')


class RecipeCreateUpdateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания и обновления рецепта."""

    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True
    )
    ingredients = RecipeIngredientCreateSerializer(many=True)
    image = Base64ImageField()
    cooking_time = serializers.IntegerField(min_value=1)

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'ingredients', 'image',
            'name', 'text', 'cooking_time'
        )

    def validate_ingredients(self, value):
        """Проверка ингредиентов: не пусто, нет дублей."""
        if not value:
            raise ValidationError('Добавьте хотя бы один ингредиент')

        ingredient_ids = [item['id'].id for item in value]
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise ValidationError('Ингредиенты не должны повторяться')

        return value

    def validate_tags(self, value):
        """Проверка тегов: не пусто, нет дублей."""
        if not value:
            raise ValidationError('Добавьте хотя бы один тег')

        if len(value) != len(set(value)):
            raise ValidationError('Теги не должны повторяться')

        return value

    def _save_ingredients(self, recipe, ingredients):
        """Сохранение ингредиентов рецепта."""
        RecipeIngredient.objects.bulk_create([
            RecipeIngredient(
                recipe=recipe,
                ingredient_id=item['id'].id,
                amount=item['amount']
            )
            for item in ingredients
        ])

    def create(self, validated_data):
        """Создание рецепта с ингредиентами и тегами."""
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        validated_data['author'] = self.context['request'].user
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        self._save_ingredients(recipe, ingredients)
        return recipe

    def update(self, instance, validated_data):
        """Обновление рецепта."""
        ingredients = validated_data.pop('ingredients', None)
        tags = validated_data.pop('tags', None)

        # Временная отладка
        print("=== DEBUG UPDATE ===")
        print(f"Request data: {self.context['request'].data}")
        print(f"Ingredients from validated_data: {ingredients}")
        print(f"Tags from validated_data: {tags}")

        instance = super().update(instance, validated_data)

        if tags is not None:
            print(f"Setting tags: {tags}")
            instance.tags.set(tags)

        if ingredients is not None:
            print(f"Deleting old ingredients, saving new: {ingredients}")
            instance.recipe_ingredients.all().delete()
            self._save_ingredients(instance, ingredients)

        return instance

    def to_representation(self, instance):
        """Возврат полного представления рецепта после создания/обновления."""
        return RecipeListSerializer(instance, context=self.context).data


class RecipeMinifiedSerializer(serializers.ModelSerializer):
    """Сериализатор для краткого отображения рецепта."""

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class UserWithRecipesSerializer(UserSerializer):
    """Сериализатор для пользователя с рецептами (подписки)."""

    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(read_only=True)

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ('recipes', 'recipes_count')

    def get_recipes(self, obj):
        """Получение рецептов пользователя с ограничением по limit."""
        request = self.context.get('request')
        recipes = obj.recipes.all()

        limit = request.query_params.get('recipes_limit')
        if limit and limit.isdigit():
            recipes = list(recipes)[:int(limit)]
        return RecipeMinifiedSerializer(recipes, many=True).data


class SubscribeSerializer(serializers.Serializer):
    """Сериализатор для подписки/отписки."""

    def validate(self, data):
        """Проверка: нельзя подписаться на себя или повторно."""
        request = self.context['request']
        author = self.context.get('author')

        if request.user == author:
            raise ValidationError('Нельзя подписаться на самого себя')

        if author.following.filter(user=request.user).exists():
            raise ValidationError('Вы уже подписаны на этого пользователя')

        return data


class FavoriteShoppingCartSerializer(serializers.Serializer):
    """Базовый сериализатор для избранного и списка покупок."""

    def validate(self, data):
        """Проверка: рецепт уже добавлен."""
        request = self.context['request']
        recipe = self.context.get('recipe')
        model = self.context.get('model')  # Модель передаём через context

        if model.objects.filter(user=request.user, recipe=recipe).exists():
            raise ValidationError('Рецепт уже добавлен')

        return data


class SetAvatarSerializer(serializers.ModelSerializer):
    """Сериализатор для установки аватара."""

    avatar = Base64ImageField()

    class Meta:
        model = User
        fields = ('avatar',)


class SetPasswordSerializer(serializers.Serializer):
    """Сериализатор для смены пароля."""

    current_password = serializers.CharField()
    new_password = serializers.CharField(min_length=8)

    def validate_current_password(self, value):
        """Проверка текущего пароля."""
        user = self.context['request'].user
        if not user.check_password(value):
            raise ValidationError('Неверный текущий пароль')
        return value
