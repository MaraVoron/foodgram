from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.pagination import PageNumberPagination

from recipes.models import (
    Tag, Ingredient, Recipe, RecipeIngredient,
    Favorite, ShoppingCart, Subscription, ShortLink
)
from users.models import User
from .serializers import (
    TagSerializer, IngredientSerializer, RecipeSerializer,
    RecipeCreateSerializer, SubscriptionSerializer,
    ShortLinkSerializer, AvatarSerializer
)
from .filters import RecipeFilter, IngredientFilter
from .permissions import IsAuthorOrReadOnly


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для просмотра тегов."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (permissions.AllowAny,)
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для просмотра и поиска ингредиентов."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (permissions.AllowAny,)
    pagination_class = None
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter


class RecipeViewSet(viewsets.ModelViewSet):
    """Вьюсет для работы с рецептами."""

    queryset = Recipe.objects.all()
    permission_classes = (IsAuthorOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    pagination_class = PageNumberPagination

    def get_serializer_class(self):
        """Выбирает сериализатор в зависимости от действия."""
        if self.action in ('create', 'partial_update', 'update'):
            return RecipeCreateSerializer
        return RecipeSerializer

    def perform_create(self, serializer):
        """Сохраняет автора рецепта при создании."""
        serializer.save(author=self.request.user)

    @action(detail=True, methods=['post', 'delete'])
    def favorite(self, request, pk=None):
        """Добавляет или удаляет рецепт из избранного."""
        recipe = self.get_object()
        if request.method == 'POST':
            obj, created = Favorite.objects.get_or_create(
                user=request.user, recipe=recipe
            )
            if not created:
                return Response(
                    {'error': 'Рецепт уже в избранном'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            return Response(
                RecipeSerializer(recipe, context={'request': request}).data,
                status=status.HTTP_201_CREATED
            )
        Favorite.objects.filter(user=request.user, recipe=recipe).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post', 'delete'])
    def shopping_cart(self, request, pk=None):
        """Добавляет или удаляет рецепт из списка покупок."""
        recipe = self.get_object()
        if request.method == 'POST':
            obj, created = ShoppingCart.objects.get_or_create(
                user=request.user, recipe=recipe
            )
            if not created:
                return Response(
                    {'error': 'Рецепт уже в списке покупок'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            return Response(
                RecipeSerializer(recipe, context={'request': request}).data,
                status=status.HTTP_201_CREATED
            )
        ShoppingCart.objects.filter(user=request.user, recipe=recipe).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'])
    def download_shopping_cart(self, request):
        """Скачивает список покупок в виде текстового файла."""
        ingredients = (
            request.user.shopping_cart
            .values(
                'recipe__recipe_ingredients__ingredient__name',
                'recipe__recipe_ingredients__ingredient__measurement_unit',
            )
            .annotate(total_amount=Sum('recipe__recipe_ingredients__amount'))
        )
        text = 'Список покупок:\n\n'
        for item in ingredients:
            name = item['recipe__recipe_ingredients__ingredient__name']
            unit = item[
                'recipe__recipe_ingredients__ingredient__measurement_unit']
            amount = item['total_amount']
            text += f'{name} ({unit}) — {amount}\n'
        response = HttpResponse(text, content_type='text/plain')
        response['Content-Disposition'] = (
            'attachment; filename="shopping_cart.txt"'
        )
        return response

    @action(detail=True, methods=['get'], url_path='get-link')
    def get_link(self, request, pk=None):
        """Генерирует короткую ссылку на рецепт."""
        recipe = self.get_object()
        short_link, _ = ShortLink.objects.get_or_create(recipe=recipe)
        return Response(
            ShortLinkSerializer(short_link, context={'request': request}).data
        )


class SubscriptionViewSet(viewsets.GenericViewSet):
    """Вьюсет для управления подписками."""

    permission_classes = (permissions.IsAuthenticated,)
    pagination_class = PageNumberPagination

    @action(detail=False, methods=['get'])
    def subscriptions(self, request):
        """Возвращает список подписок текущего пользователя."""
        user = request.user
        subscriptions = Subscription.objects.filter(user=user)
        page = self.paginate_queryset(subscriptions)
        serializer = SubscriptionSerializer(
            page, many=True, context={'request': request}
        )
        return self.get_paginated_response(serializer.data)

    @action(detail=True, methods=['post', 'delete'])
    def subscribe(self, request, pk=None):
        """Подписывает или отписывает пользователя от автора."""
        author = User.objects.get(pk=pk)
        if request.method == 'POST':
            if request.user == author:
                return Response(
                    {'error': 'Нельзя подписаться на себя'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            subscription, created = Subscription.objects.get_or_create(
                user=request.user, author=author
            )
            if not created:
                return Response(
                    {'error': 'Вы уже подписаны'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            return Response(
                SubscriptionSerializer(
                    subscription, context={'request': request}
                ).data,
                status=status.HTTP_201_CREATED
            )
        Subscription.objects.filter(
            user=request.user, author=author
        ).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


def short_link_redirect(request, code):
    """Перенаправляет с короткой ссылки на страницу рецепта."""
    short_link = get_object_or_404(ShortLink, code=code)
    return redirect(f'/recipes/{short_link.recipe.id}/')


class AvatarView(APIView):
    """Вью для загрузки и удаления аватара."""

    permission_classes = (permissions.IsAuthenticated,)

    def put(self, request):
        """Загружает или обновляет аватар пользователя."""
        serializer = AvatarSerializer(request.user, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        """Удаляет аватар пользователя."""
        request.user.avatar.delete(save=True)
        return Response(status=status.HTTP_204_NO_CONTENT)
