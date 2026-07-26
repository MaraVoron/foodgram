from django_filters import rest_framework as filters

from recipes.models import Recipe, Ingredient


class RecipeFilter(filters.FilterSet):
    """Фильтр для рецептов по тегам, автору, избранному и списку покупок."""

    tags = filters.AllValuesMultipleFilter(field_name='tags__slug')
    author = filters.NumberFilter(field_name='author__id')
    is_favorited = filters.BooleanFilter(method='filter_is_favorited')
    is_in_shopping_cart = filters.BooleanFilter(
        method='filter_is_in_shopping_cart')

    class Meta:
        """Основной класс."""

        model = Recipe
        fields = ('tags', 'author', 'is_favorited', 'is_in_shopping_cart')

    def filter_is_favorited(self, queryset, name, value):
        """Фильтрует рецепты по наличию в избранном у текущего пользователя."""
        if value and self.request.user.is_authenticated:
            return queryset.filter(favorites__user=self.request.user)
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        """Фильтрует рецепты по наличию в списке покупок."""
        if value and self.request.user.is_authenticated:
            return queryset.filter(shopping_cart__user=self.request.user)
        return queryset


class IngredientFilter(filters.FilterSet):
    """Фильтр для поиска ингредиентов по названию."""

    name = filters.CharFilter(lookup_expr='istartswith')

    class Meta:
        """Основной класс."""

        model = Ingredient
        fields = ('name',)
