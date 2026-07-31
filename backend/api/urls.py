from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    AvatarView, IngredientViewSet, RecipeViewSet, TagViewSet, UserViewSet
)

router = DefaultRouter()
router.register('users', UserViewSet, basename='users')
router.register('tags', TagViewSet, basename='tags')
router.register('ingredients', IngredientViewSet, basename='ingredients')
router.register('recipes', RecipeViewSet, basename='recipes')

urlpatterns = [
    path('', include(router.urls)),
    path('users/me/avatar/', AvatarView.as_view(), name='avatar'),
]
