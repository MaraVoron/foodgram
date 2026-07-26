import json
import os

from django.core.management.base import BaseCommand

from recipes.models import Ingredient, Tag


class Command(BaseCommand):
    """Команда для загрузки ингредиентов и тегов в базу данных."""

    help = 'Загрузка ингредиентов и тегов в базу данных'

    def handle(self, *args, **options):
        """Загружает данные из JSON-файла."""
        ingredients_path = os.path.join('data', 'ingredients.json')

        if os.path.exists(ingredients_path):
            with open(ingredients_path, 'r', encoding='utf-8') as f:
                ingredients = json.load(f)
                for item in ingredients:
                    Ingredient.objects.get_or_create(
                        name=item['name'],
                        measurement_unit=item['measurement_unit'],
                    )
            self.stdout.write(self.style.SUCCESS(
                f'Загружено {len(ingredients)} ингредиентов'
            ))
        else:
            self.stdout.write(self.style.WARNING(
                f'Файл {ingredients_path} не найден'
            ))

        tags_data = [
            {'name': 'Завтрак', 'slug': 'breakfast'},
            {'name': 'Обед', 'slug': 'lunch'},
            {'name': 'Ужин', 'slug': 'dinner'},
        ]
        for tag_data in tags_data:
            Tag.objects.get_or_create(**tag_data)
        self.stdout.write(self.style.SUCCESS(
            f'Загружено {len(tags_data)} тегов'
        ))
