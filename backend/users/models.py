from django.contrib.auth.models import AbstractUser
from django.db import models

from .constants import USER_NAME_FIELD_MAX_LENGTH


class User(AbstractUser):
    """Кастомная модель пользователя с email в качестве логина."""

    email = models.EmailField(
        verbose_name='Email',
        unique=True,
    )
    first_name = models.CharField(
        verbose_name='Имя', max_length=USER_NAME_FIELD_MAX_LENGTH,
    )
    last_name = models.CharField(
        verbose_name='Фамилия', max_length=USER_NAME_FIELD_MAX_LENGTH,
    )
    avatar = models.ImageField(
        upload_to='avatars/',
        blank=True,
        null=True,
        verbose_name='Аватар',
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        """Основной класс."""

        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('username',)

    def __str__(self):
        """Функция вывода."""
        return self.email
