import base64

from django.core.files.base import ContentFile
from rest_framework import serializers

from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Subscription, Tag)
from users.models import User


class Base64ImageField(serializers.ImageField):
    """Кастомное поле для обработки картинок в base64."""

    def to_internal_value(self, data):
        """Декодирует base64-строку в файл изображения."""
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)
        return super().to_internal_value(data)


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор для отображения пользователя."""

    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        """Основной класс."""

        model = User
        fields = ('email', 'id', 'username', 'first_name', 'last_name',
                  'avatar', 'is_subscribed')

    def get_is_subscribed(self, obj):
        """Проверяет подписку пользователя на автора."""
        request = self.context.get('request')
        return bool(
            request and request.user.is_authenticated and
            Subscription.objects.filter(
                user=request.user, author=obj).exists()
        )


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для тегов."""

    class Meta:
        """Основной класс."""

        model = Tag
        fields = ('id', 'name', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для ингредиентов."""

    class Meta:
        """Основной класс."""

        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class RecipeIngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для ингредиентов внутри рецепта."""

    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all(),
                                            source='ingredient')
    name = serializers.CharField(source='ingredient.name', read_only=True)
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit', read_only=True)

    class Meta:
        """Основной класс."""

        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для чтения рецепта."""

    author = UserSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    ingredients = RecipeIngredientSerializer(
        many=True, source='recipe_ingredients', read_only=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        """Основной класс."""

        model = Recipe
        fields = (
            'id', 'author', 'name', 'image', 'text', 'ingredients', 'tags',
            'cooking_time', 'is_favorited', 'is_in_shopping_cart'
        )

    def get_is_favorited(self, obj):
        """Проверяет добавлен ли рецепт в избранное."""
        request = self.context.get('request')
        return bool(
            request and request.user.is_authenticated and
            Favorite.objects.filter(user=request.user, recipe=obj).exists()
        )

    def get_is_in_shopping_cart(self, obj):
        """Проверяет добавлен ли продукт в список покупок."""
        request = self.context.get('request')
        return bool(
            request and request.user.is_authenticated and
            ShoppingCart.objects.filter(
                user=request.user, recipe=obj).exists()
        )


class RecipeCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания и редактирования рецепта."""

    image = Base64ImageField()
    tags = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all(),
    )
    ingredients = RecipeIngredientSerializer(
        many=True, source='recipe_ingredients')

    class Meta:
        """Основной класс."""

        model = Recipe
        fields = ('id', 'name', 'image', 'text', 'ingredients',
                  'tags', 'cooking_time')

    def validate(self, data):
        """Проверяет данные рецепта при сохранении."""
        if 'tags' not in self.initial_data:
            raise serializers.ValidationError(
                {'tags': 'Это поле обязательно.'})
        if 'ingredients' not in self.initial_data:
            raise serializers.ValidationError(
                {'ingredients': 'Это поле обязательно.'})

        tags = data.get('tags')
        if not tags:
            raise serializers.ValidationError(
                {'tags': 'Нужно добавить хотя бы один тег.'})
        if len(tags) != len(set(tags)):
            raise serializers.ValidationError(
                {'tags': 'Теги не должны повторяться.'})

        ingredients = data.get('recipe_ingredients')
        if not ingredients:
            raise serializers.ValidationError(
                {'ingredients': 'Нужно добавить хотя бы один ингредиент.'})
        ingredient_ids = [item['ingredient'].id for item in ingredients]
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise serializers.ValidationError(
                {'ingredients': 'Ингредиенты не должны повторяться.'})

        return data

    def create(self, validated_data):
        """Создание рецепта."""
        ingredients_data = validated_data.pop('recipe_ingredients')
        tags_data = validated_data.pop('tags')
        recipe = Recipe.objects.create(
            author=self.context['request'].user, **validated_data
        )
        recipe.tags.set(tags_data)
        for ingredient_data in ingredients_data:
            RecipeIngredient.objects.create(
                recipe=recipe,
                ingredient=ingredient_data['ingredient'],
                amount=ingredient_data['amount'],
            )
        return recipe

    def update(self, instance, validated_data):
        """Обновляет существующий рецепт."""
        ingredients_data = validated_data.pop('recipe_ingredients')
        tags_data = validated_data.pop('tags')
        instance.tags.set(tags_data)
        instance.recipe_ingredients.all().delete()
        for ingredient_data in ingredients_data:
            RecipeIngredient.objects.create(
                recipe=instance,
                ingredient=ingredient_data['ingredient'],
                amount=ingredient_data['amount'],
            )
        return super().update(instance, validated_data)


class ShortRecipeSerializer(serializers.ModelSerializer):
    """Краткий сериализатор рецепта для вложенных списков."""

    class Meta:
        """Основной класс."""

        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class SubscriptionSerializer(UserSerializer):
    """Для отображения: автор + его рецепты (с учётом лимита)."""

    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(
        source='recipes.count', read_only=True)

    class Meta:
        """Общий класс."""

        model = User
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name',
            'avatar', 'is_subscribed', 'recipes', 'recipes_count',
        )

    def get_recipes(self, obj):
        """Возвращает список рецептов автора с учётом лимита."""
        request = self.context.get('request')
        recipes = obj.recipes.all()
        recipes_limit = request.query_params.get(
            'recipes_limit') if request else None
        if (
            recipes_limit and
            recipes_limit.isdigit() and
            int(recipes_limit) > 0
        ):
            recipes = recipes[:int(recipes_limit)]
        return ShortRecipeSerializer(
            recipes, many=True, context=self.context).data


class SubscriptionCreateSerializer(serializers.ModelSerializer):
    """Для создания подписки: валидация + сохранение."""

    class Meta:
        """Общий класс."""

        model = Subscription
        fields = ('user', 'author')

    def validate(self, data):
        """Проверяет данные перед созданием подписки."""
        user, author = data['user'], data['author']
        if user == author:
            raise serializers.ValidationError(
                'Нельзя подписаться на самого себя.')
        if Subscription.objects.filter(user=user, author=author).exists():
            raise serializers.ValidationError('Вы уже подписаны.')
        return data

    def to_representation(self, instance):
        """Форматирует ответ."""
        return SubscriptionSerializer(
            instance.author, context=self.context).data


class AvatarSerializer(serializers.ModelSerializer):
    """Сериализатор для загрузки аватара."""

    avatar = Base64ImageField(required=True)

    class Meta:
        """Основной класс."""

        model = User
        fields = ('avatar',)

    def to_representation(self, instance):
        """Возвращает ссылку на аватар."""
        request = self.context.get('request')
        if instance.avatar:
            return {'avatar': request.build_absolute_uri(instance.avatar.url)}
        return {'avatar': None}


class FavoriteSerializer(serializers.ModelSerializer):
    """Сериализатор для добавления рецепта в избранное."""

    class Meta:
        """Общий класс."""

        model = Favorite
        fields = ('user', 'recipe')

    def validate(self, data):
        """Проверяет, что рецепт ещё не в избранном."""
        if Favorite.objects.filter(**data).exists():
            raise serializers.ValidationError('Рецепт уже в избранном.')
        return data

    def to_representation(self, instance):
        """Возвращает краткую информацию о рецепте."""
        return ShortRecipeSerializer(
            instance.recipe, context=self.context).data


class ShoppingCartSerializer(serializers.ModelSerializer):
    """Сериализатор для добавления рецепта в список покупок."""

    class Meta:
        """Общий класс."""

        model = ShoppingCart
        fields = ('user', 'recipe')

    def validate(self, data):
        """Проверяет, что рецепт ещё не в списке покупок."""
        if ShoppingCart.objects.filter(**data).exists():
            raise serializers.ValidationError('Рецепт уже в списке покупок.')
        return data

    def to_representation(self, instance):
        """Возвращает краткую информацию о рецепте."""
        return ShortRecipeSerializer(
            instance.recipe, context=self.context).data
