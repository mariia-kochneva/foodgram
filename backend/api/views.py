from django.db.models import Count
from django.shortcuts import get_object_or_404
from django.http import HttpResponse

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from django.urls import reverse
from django.shortcuts import redirect

from users.models import User, Subscription
from recipes.models import (
    Tag, Ingredient, Recipe, Favorite, ShoppingCart
)
from .permissions import IsAuthorOrReadOnly, IsAuthenticatedOnly
from .serializers import (
    TagSerializer,
    IngredientSerializer,
    RecipeListSerializer,
    RecipeCreateUpdateSerializer,
    RecipeMinifiedSerializer,
    UserSerializer,
    UserWithRecipesSerializer,
    SubscribeSerializer,
    SetAvatarSerializer,
    SetPasswordSerializer,
)
from .filters import RecipeFilter, IngredientFilter
from .utils import get_shopping_cart_ingredients, generate_shopping_cart_pdf


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """Теги. Только чтение."""
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [AllowAny]
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Ингредиенты. Только чтение, поиск по названию."""
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = [AllowAny]
    pagination_class = None
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter


class RecipeShortLinkView(APIView):
    """Редирект по короткой ссылке на рецепт."""
    permission_classes = [AllowAny]

    def get(self, request, pk):
        get_object_or_404(Recipe, pk=pk)
        return redirect(request.build_absolute_uri(f'/recipes/{pk}'))


class RecipeViewSet(viewsets.ModelViewSet):
    """Рецепты."""
    queryset = Recipe.objects.select_related('author').prefetch_related(
        'tags',
        'recipe_ingredients__ingredient',
        'favorites',
        'shopping_cart',
    )
    permission_classes = [IsAuthorOrReadOnly]
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    http_method_names = ['get', 'post', 'patch', 'delete']

    def get_serializer_class(self):
        """Выбор сериализатора в зависимости от действия."""
        if self.action in ('list', 'retrieve'):
            return RecipeListSerializer
        return RecipeCreateUpdateSerializer

    def perform_create(self, serializer):
        """Создание рецепта с привязкой автора."""
        serializer.save(author=self.request.user)

    def _manage_relation(self, request, pk, model, serializer_class):
        """
        Универсальный метод для управления связями (избранное/покупки).
        """
        recipe = self.get_object()
        user = request.user

        if request.method == 'POST':
            obj, created = model.objects.get_or_create(
                user=user, recipe=recipe
            )
            if not created:
                return Response(
                    {'error': 'Уже добавлено'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            serializer = serializer_class(recipe, context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        deleted, _ = model.objects.filter(user=user, recipe=recipe).delete()
        if not deleted:
            return Response(
                {'error': 'Не найдено'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        methods=['POST', 'DELETE'],
        detail=True,
        permission_classes=[IsAuthenticatedOnly],
    )
    def favorite(self, request, pk=None):
        """Добавление/удаление рецепта в избранное."""
        return self._manage_relation(
            request, pk, Favorite, RecipeMinifiedSerializer
        )

    @action(
        methods=['POST', 'DELETE'],
        detail=True,
        permission_classes=[IsAuthenticatedOnly],
    )
    def shopping_cart(self, request, pk=None):
        """Добавление/удаление рецепта в список покупок."""
        return self._manage_relation(
            request, pk, ShoppingCart, RecipeMinifiedSerializer
        )

    @action(
        methods=['GET'],
        detail=False,
        permission_classes=[IsAuthenticatedOnly],
    )
    def download_shopping_cart(self, request):
        """Скачать список покупок в формате PDF."""
        ingredients = get_shopping_cart_ingredients(request.user)
        buffer = generate_shopping_cart_pdf(request.user, ingredients)
        response = HttpResponse(buffer, content_type='application/pdf')
        response['Content-Disposition'] = (
            'attachment; filename="shopping_cart.pdf"'
        )
        return response

    @action(
        methods=['GET'],
        detail=True,
        permission_classes=[AllowAny],
        url_path='get-link',
    )
    def get_link(self, request, pk=None):
        """Получить короткую ссылку на рецепт."""
        recipe = self.get_object()
        relative_url = reverse('recipe-short-link', kwargs={'pk': recipe.id})
        full_url = request.build_absolute_uri(relative_url)
        return Response({'short-link': full_url})


class UserViewSet(viewsets.ModelViewSet):
    """Пользователи."""
    queryset = User.objects.prefetch_related('recipes').all()
    permission_classes = [AllowAny]
    filter_backends = (filters.SearchFilter,)
    search_fields = ('username', 'email')
    lookup_field = 'id'
    http_method_names = ['get', 'post', 'put', 'patch', 'delete']

    def get_serializer_class(self):
        """Выбор сериализатора в зависимости от действия."""
        if self.action == 'create':
            return UserRegistrationSerializer
        if self.action == 'subscriptions':
            return UserWithRecipesSerializer
        if self.action == 'subscribe':
            return SubscribeSerializer
        return UserSerializer

    def perform_create(self, serializer):
        serializer.save()

    @action(
        methods=['GET'],
        detail=False,
        permission_classes=[IsAuthenticated],
    )
    def me(self, request):
        """Профиль текущего пользователя."""
        serializer = UserSerializer(request.user, context={'request': request})
        return Response(serializer.data)

    @action(
        methods=['PUT', 'DELETE'],
        detail=False,
        permission_classes=[IsAuthenticated],
        url_path='me/avatar',
    )
    def avatar(self, request):
        """Установка/удаление аватара."""
        user = request.user

        if request.method == 'PUT':
            serializer = SetAvatarSerializer(user, data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response({'avatar': user.avatar.url})

        if user.avatar:
            user.avatar.delete(save=True)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        methods=['POST'],
        detail=False,
        permission_classes=[IsAuthenticated],
        url_path='set_password',
    )
    def set_password(self, request):
        """Смена пароля."""
        serializer = SetPasswordSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        request.user.set_password(serializer.validated_data['new_password'])
        request.user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        methods=['GET'],
        detail=False,
        permission_classes=[IsAuthenticated],
        url_path='subscriptions',
    )
    def subscriptions(self, request):
        """Список подписок текущего пользователя."""
        authors = User.objects.filter(
            following__user=request.user
        ).prefetch_related('recipes').annotate(
            recipes_count=Count('recipes')
        )
        page = self.paginate_queryset(authors)
        serializer = UserWithRecipesSerializer(
            page, many=True, context={'request': request}
        )
        return self.get_paginated_response(serializer.data)

    @action(
        methods=['POST', 'DELETE'],
        detail=True,
        permission_classes=[IsAuthenticatedOnly],
    )
    def subscribe(self, request, id=None):
        """Подписка/отписка на пользователя."""
        author = get_object_or_404(
            User.objects.annotate(recipes_count=Count('recipes')),
            id=id
        )
        user = request.user

        if request.method == 'POST':
            if user == author:
                return Response(
                    {'error': 'Нельзя подписаться на самого себя'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            obj, created = Subscription.objects.get_or_create(
                user=user, author=author
            )
            if not created:
                return Response(
                    {'error': 'Вы уже подписаны'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            serializer = UserWithRecipesSerializer(
                author, context={'request': request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        deleted, _ = Subscription.objects.filter(
            user=user, author=author
        ).delete()
        if not deleted:
            return Response(
                {'error': 'Подписка не найдена'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(status=status.HTTP_204_NO_CONTENT)
