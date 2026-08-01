from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect

from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from recipes.models import (
    Favorite, Ingredient, Recipe, ShoppingCart,
    Subscription, Tag
)
from users.models import User
from .filters import IngredientFilter, RecipeFilter
from .pagination import LimitPagination
from .permissions import IsAuthorOrReadOnly
from .serializers import (
    AvatarSerializer, IngredientSerializer, RecipeCreateSerializer,
    RecipeSerializer, SubscriptionSerializer, TagSerializer,
    FavoriteSerializer, ShoppingCartSerializer, SubscriptionCreateSerializer
)


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
    pagination_class = LimitPagination

    def get_serializer_class(self):
        """Выбирает сериализатор в зависимости от действия."""
        if self.action in ('create', 'partial_update', 'update'):
            return RecipeCreateSerializer
        return RecipeSerializer

    @action(detail=True, methods=['post'],
            permission_classes=[permissions.IsAuthenticated])
    def favorite(self, request, pk=None):
        """Добавляет рецепт в избранное."""
        recipe = self.get_object()
        serializer = FavoriteSerializer(
            data={'user': request.user.id, 'recipe': recipe.id},
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @favorite.mapping.delete
    def delete_favorite(self, request, pk=None):
        """Удаляет рецепт из избранного."""
        recipe = self.get_object()
        deleted, _ = Favorite.objects.filter(
            user=request.user, recipe=recipe
        ).delete()
        if not deleted:
            return Response(
                {'error': 'Рецепт не в избранном'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post'],
            permission_classes=[permissions.IsAuthenticated])
    def shopping_cart(self, request, pk=None):
        """Добавляет рецепт в список покупок."""
        recipe = self.get_object()
        serializer = ShoppingCartSerializer(
            data={'user': request.user.id, 'recipe': recipe.id},
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @shopping_cart.mapping.delete
    def delete_shopping_cart(self, request, pk=None):
        """Удаляет рецепт из списка покупок."""
        recipe = self.get_object()
        deleted, _ = ShoppingCart.objects.filter(
            user=request.user, recipe=recipe
        ).delete()
        if not deleted:
            return Response(
                {'error': 'Рецепт не в списке покупок'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'],
            permission_classes=[permissions.IsAuthenticated])
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
                'recipe__recipe_ingredients__ingredient__measurement_unit'
            ]
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
        return Response({
            'short-link': request.build_absolute_uri(
                f'/s/{recipe.short_code}/'
            )
        })

    def create(self, request, *args, **kwargs):
        """Создаёт рецепт и возвращает его в формате чтения."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        read_serializer = RecipeSerializer(
            serializer.instance, context=self.get_serializer_context()
        )
        return Response(read_serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        """Обновляет рецепт и возвращает его в формате чтения."""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(
            instance, data=request.data, partial=partial
        )
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        read_serializer = RecipeSerializer(
            serializer.instance, context=self.get_serializer_context()
        )
        return Response(read_serializer.data)


class AvatarView(APIView):
    """Вью для загрузки и удаления аватара."""

    permission_classes = (permissions.IsAuthenticated,)

    def put(self, request):
        """Загружает или обновляет аватар пользователя."""
        serializer = AvatarSerializer(
            request.user, data=request.data, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request):
        """Удаляет аватар пользователя."""
        request.user.avatar.delete(save=True)
        return Response(status=status.HTTP_204_NO_CONTENT)


class UserViewSet(DjoserUserViewSet):
    """Вьюсет пользователя с раздельными правами и подписками."""

    @action(['get'], detail=False,
            permission_classes=[permissions.IsAuthenticated])
    def me(self, request, *args, **kwargs):
        """Текущий пользователь."""
        return super().me(request, *args, **kwargs)

    @action(detail=False, methods=['get'],
            permission_classes=[permissions.IsAuthenticated],
            pagination_class=LimitPagination)
    def subscriptions(self, request):
        """Возвращает список подписок текущего пользователя."""
        authors = User.objects.filter(following__user=request.user)
        page = self.paginate_queryset(authors)
        serializer = SubscriptionSerializer(
            page, many=True, context={'request': request}
        )
        return self.get_paginated_response(serializer.data)

    @action(detail=True, methods=['post'],
            permission_classes=[permissions.IsAuthenticated])
    def subscribe(self, request, id=None):
        """Подписывает пользователя на автора."""
        author = get_object_or_404(User, pk=id)
        serializer = SubscriptionCreateSerializer(
            data={'user': request.user.id, 'author': author.id},
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @subscribe.mapping.delete
    def delete_subscribe(self, request, id=None):
        """Отписывает пользователя от автора."""
        author = get_object_or_404(User, pk=id)
        deleted, _ = Subscription.objects.filter(
            user=request.user, author=author
        ).delete()
        if not deleted:
            return Response(
                {'error': 'Вы не подписаны'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(status=status.HTTP_204_NO_CONTENT)


def short_link_redirect(request, code):
    """Перенаправляет с короткой ссылки на страницу рецепта."""
    recipe = get_object_or_404(Recipe, short_code=code)
    return redirect(f'/recipes/{recipe.id}/')
