from django.contrib import admin

from .models import Tag, Ingredient, Recipe, RecipeIngredient
from .models import Favorite, ShoppingCart, Subscription


class RecipeIngredientInline(admin.TabularInline):
    """Инлайн-форма для редактирования ингредиентов рецепта."""

    model = RecipeIngredient
    extra = 1
    min_num = 1


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Администрирование тегов."""

    list_display = ('name', 'slug')
    search_fields = ('name',)


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    """Администрирование ингредиентов."""

    list_display = ('name', 'measurement_unit')
    search_fields = ('name',)


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """Администрирование рецептов."""

    list_display = ('name', 'author', 'cooking_time', 'favorites_count')
    list_filter = ('tags',)
    search_fields = ('name', 'author__email', 'author__username')
    inlines = (RecipeIngredientInline,)

    @admin.display(description='В избранном')
    def favorites_count(self, obj):
        """Возвращает количество добавлений рецепта в избранное."""
        return obj.favorites.count()


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    """Администрирование избранного."""

    list_display = ('user', 'recipe')


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    """Администрирование списка покупок."""

    list_display = ('user', 'recipe')


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    """Администрирование подписок."""

    list_display = ('user', 'author')
