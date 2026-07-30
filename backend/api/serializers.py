import base64

from django.core.files.base import ContentFile
from rest_framework import serializers

from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, ShortLink, Subscription, Tag)
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


class UserCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для регистрации пользователя."""

    class Meta:
        """Основной класс."""

        model = User
        fields = ('email', 'id', 'username', 'first_name',
                  'last_name', 'password')
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        """Создаёт нового пользователя с хешированным паролем."""
        user = User(
            email=validated_data['email'],
            username=validated_data['username'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
        )
        user.set_password(validated_data['password'])
        user.save()
        return user


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор для отображения пользователя."""

    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        """Основной класс."""

        model = User
        fields = ('email', 'id', 'username', 'first_name', 'last_name',
                  'avatar', 'is_subscribed')

    def get_is_subscribed(self, obj):
        """Проверяет, подписан ли текущий пользователь на автора."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Subscription.objects.filter(
                user=request.user, author=obj).exists()
        return False


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
        """Проверяет, добавлен ли рецепт в избранное."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Favorite.objects.filter(
                user=request.user, recipe=obj).exists()
        return False

    def get_is_in_shopping_cart(self, obj):
        """Проверяет, добавлен ли рецепт в список покупок."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return ShoppingCart.objects.filter(
                user=request.user, recipe=obj).exists()
        return False


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

    def validate_ingredients(self, value):
        """Проверяет, что ингредиенты не пустые и не дублируются."""
        if not value:
            raise serializers.ValidationError(
                'Нужно добавить хотя бы один ингредиент')
        ingredient_ids = [item['ingredient'].id for item in value]
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise serializers.ValidationError(
                'Ингредиенты не должны повторяться')
        return value

    def create(self, validated_data):
        """Создаёт рецепт с ингредиентами и тегами."""
        ingredients_data = validated_data.pop('recipe_ingredients')
        tags_data = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags_data)
        for ingredient_data in ingredients_data:
            RecipeIngredient.objects.create(
                recipe=recipe,
                ingredient=ingredient_data['ingredient'],
                amount=ingredient_data['amount'],
            )
        return recipe

    def update(self, instance, validated_data):
        """Обновляет рецепт, ингредиенты и теги."""
        ingredients_data = validated_data.pop('recipe_ingredients', None)
        tags_data = validated_data.pop('tags', None)

        instance.name = validated_data.get('name', instance.name)
        instance.text = validated_data.get('text', instance.text)
        instance.cooking_time = validated_data.get(
            'cooking_time', instance.cooking_time)
        if 'image' in validated_data:
            instance.image = validated_data['image']
        instance.save()

        if tags_data is not None:
            instance.tags.set(tags_data)

        if ingredients_data is not None:
            instance.recipe_ingredients.all().delete()
            for ingredient_data in ingredients_data:
                RecipeIngredient.objects.create(
                    recipe=instance,
                    ingredient=ingredient_data['ingredient'],
                    amount=ingredient_data['amount'],
                )
        return instance

    def validate_tags(self, value):
        """Проверяет теги на дубликаты."""
        if not value:
            raise serializers.ValidationError(
                'Нужно добавить хотя бы один тег')
        if len(value) != len(set(value)):
            raise serializers.ValidationError(
                'Теги не должны повторяться')
        return value

    def validate(self, data):
        """Проверяет обязательные поля при PATCH."""
        if 'tags' not in self.initial_data:
            raise serializers.ValidationError(
                {'tags': 'Это поле обязательно.'})
        if 'ingredients' not in self.initial_data:
            raise serializers.ValidationError(
                {'ingredients': 'Это поле обязательно.'})
        return data


class ShortRecipeSerializer(serializers.ModelSerializer):
    """Краткий сериализатор рецепта для вложенных списков."""

    class Meta:
        """Основной класс."""

        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class SubscriptionSerializer(serializers.ModelSerializer):
    """Сериализатор для отображения подписок."""

    email = serializers.CharField(source='author.email', read_only=True)
    id = serializers.IntegerField(source='author.id', read_only=True)
    username = serializers.CharField(source='author.username', read_only=True)
    first_name = serializers.CharField(
        source='author.first_name', read_only=True)
    last_name = serializers.CharField(
        source='author.last_name', read_only=True)
    avatar = serializers.ImageField(source='author.avatar', read_only=True)
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(
        source='author.recipes.count', read_only=True)

    class Meta:
        """Основной класс."""

        model = Subscription
        fields = ('email', 'id', 'username', 'first_name', 'last_name',
                  'avatar', 'is_subscribed', 'recipes', 'recipes_count')

    def get_is_subscribed(self, obj):
        """Возвращает True для всех объектов подписки."""
        return True

    def get_recipes(self, obj):
        """Возвращает рецепты автора с учётом лимита."""
        recipes = obj.author.recipes.all()
        request = self.context.get('request')
        recipes_limit = request.query_params.get('recipes_limit')
        if recipes_limit:
            recipes = recipes[:int(recipes_limit)]
        return ShortRecipeSerializer(recipes, many=True).data


class ShortLinkSerializer(serializers.ModelSerializer):
    """Сериализатор для короткой ссылки на рецепт."""

    class Meta:
        """Метаданные сериализатора."""

        model = ShortLink
        fields = ()

    def to_representation(self, instance):
        """Возвращает короткую ссылку в нужном формате."""
        request = self.context.get('request')
        return {
            'short-link': request.build_absolute_uri(
                f'/s/{instance.code}/'
            )
        }


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
