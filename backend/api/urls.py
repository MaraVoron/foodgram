from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (TagViewSet, IngredientViewSet, RecipeViewSet,
                    SubscriptionViewSet, AvatarView, UserViewSet)

router = DefaultRouter()
router.register('users', UserViewSet, basename='users')
router.register('tags', TagViewSet, basename='tags')
router.register('ingredients', IngredientViewSet, basename='ingredients')
router.register('recipes', RecipeViewSet, basename='recipes')

urlpatterns = [
    path('', include(router.urls)),
    path('users/subscriptions/', SubscriptionViewSet.as_view(
        {'get': 'subscriptions'}),
        name='subscriptions'),
    path('users/me/avatar/', AvatarView.as_view(), name='avatar'),
    path('users/<int:pk>/subscribe/', SubscriptionViewSet.as_view(
        {'post': 'subscribe', 'delete': 'subscribe'}),
        name='subscribe'),

]
