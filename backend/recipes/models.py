import secrets

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from users.models import User
from .constants import (
    AMOUNT_MAX, AMOUNT_MIN, COOKING_TIME_MAX, COOKING_TIME_MIN,
    INGREDIENT_MEASUREMENT_UNIT_MAX_LENGTH, INGREDIENT_NAME_MAX_LENGTH,
    RECIPE_NAME_MAX_LENGTH, SHORT_CODE_LENGTH, TAG_NAME_MAX_LENGTH,
    TAG_SLUG_MAX_LENGTH,
)


def generate_short_code():
    """Генерирует код для короткой ссылки."""
    return secrets.token_hex(4)


class Tag(models.Model):
    """Модель тега."""

    name = models.CharField(
        verbose_name='Название', max_length=TAG_NAME_MAX_LENGTH, unique=True,
    )
    slug = models.SlugField(
        verbose_name='Слаг', max_length=TAG_SLUG_MAX_LENGTH, unique=True,
    )

    class Meta:
        """Основной класс."""

        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        """Строковое представление тега."""
        return self.name


class Ingredient(models.Model):
    """Модель ингредиента."""

    name = models.CharField(
        verbose_name='Название', max_length=INGREDIENT_NAME_MAX_LENGTH,
    )
    measurement_unit = models.CharField(
        verbose_name='Единица измерения',
        max_length=INGREDIENT_MEASUREMENT_UNIT_MAX_LENGTH,
    )

    class Meta:
        """Основной класс."""

        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'measurement_unit'],
                name='unique_ingredient_measurement_unit',
            )
        ]

    def __str__(self):
        """Строковое представление ингредиента."""
        return f'{self.name} ({self.measurement_unit})'


class Recipe(models.Model):
    """Модель рецепта."""

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор',
    )
    name = models.CharField(
        verbose_name='Название', max_length=RECIPE_NAME_MAX_LENGTH,
    )
    image = models.ImageField(
        verbose_name='Картинка', upload_to='recipes/images/',
    )
    text = models.TextField(verbose_name='Описание')
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name='Время приготовления (мин)',
        validators=[
            MinValueValidator(COOKING_TIME_MIN),
            MaxValueValidator(COOKING_TIME_MAX),
        ],
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        related_name='recipes',
        verbose_name='Ингредиенты',
    )
    tags = models.ManyToManyField(
        Tag, related_name='recipes', verbose_name='Теги',
    )
    created_at = models.DateTimeField(
        verbose_name='Дата публикации', auto_now_add=True,
    )
    short_code = models.CharField(
        max_length=SHORT_CODE_LENGTH, unique=True, editable=False, blank=True,
    )

    class Meta:
        """Основной класс."""

        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-created_at',)

    def __str__(self):
        """Строковое представление рецепта."""
        return self.name

    def save(self, *args, **kwargs):
        """Генерирует короткий код только при создании."""
        if not self.short_code:
            self.short_code = generate_short_code()
        super().save(*args, **kwargs)


class RecipeIngredient(models.Model):
    """Промежуточная модель связи рецепта и ингредиента."""

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='recipe_ingredients',
        verbose_name='Рецепт',
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='recipe_ingredients',
        verbose_name='Ингредиент',
    )
    amount = models.PositiveSmallIntegerField(
        verbose_name='Количество',
        validators=[
            MinValueValidator(AMOUNT_MIN),
            MaxValueValidator(AMOUNT_MAX),
        ],
    )

    class Meta:
        """Основной класс."""

        verbose_name = 'Ингредиент в рецепте'
        verbose_name_plural = 'Ингредиенты в рецептах'
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='unique_recipe_ingredient',
            )
        ]

    def __str__(self):
        """Строковое представление связи рецепта и ингредиента."""
        return f'{self.ingredient.name} — {self.amount}'


class Favorite(models.Model):
    """Модель избранного."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='Пользователь',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='Рецепт',
    )

    class Meta:
        """Основной класс."""

        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'], name='unique_favorite',
            )
        ]

    def __str__(self):
        """Строковое представление избранного."""
        return f'{self.user} добавил {self.recipe} в избранное'


class ShoppingCart(models.Model):
    """Модель списка покупок."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='shopping_cart',
        verbose_name='Пользователь',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='shopping_cart',
        verbose_name='Рецепт',
    )

    class Meta:
        """Основной класс."""

        verbose_name = 'Список покупок'
        verbose_name_plural = 'Список покупок'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'], name='unique_shopping_cart',
            )
        ]

    def __str__(self):
        """Строковое представление списка покупок."""
        return f'{self.user} добавил {self.recipe} в покупки'


class Subscription(models.Model):
    """Модель подписки на автора."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='Подписчик',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='Автор',
    )

    class Meta:
        """Основной класс."""

        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'], name='unique_subscription',
            )
        ]

    def __str__(self):
        """Строковое представление подписки."""
        return f'{self.user} подписан на {self.author}'
