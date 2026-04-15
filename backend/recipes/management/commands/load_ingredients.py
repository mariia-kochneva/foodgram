import csv
import os
from django.core.management.base import BaseCommand
from recipes.models import Ingredient


class Command(BaseCommand):
    help = 'Загрузка ингредиентов из CSV-файла'

    def handle(self, *args, **options):
        # Пробуем несколько путей
        possible_paths = [
            os.path.join('data', 'ingredients.csv'),
            os.path.join('..', 'data', 'ingredients.csv'),
            os.path.join('app', 'data', 'ingredients.csv'),
        ]

        file_path = None
        for path in possible_paths:
            if os.path.exists(path):
                file_path = path
                break

        if not file_path:
            self.stdout.write(
                self.style.ERROR('Файл ingredients.csv не найден')
            )
            return

        with open(file_path, 'r', encoding='utf-8') as file:
            reader = csv.reader(file)
            ingredients = []
            for row in reader:
                if len(row) >= 2:
                    ingredients.append(
                        Ingredient(
                            name=row[0].strip(),
                            measurement_unit=row[1].strip()
                        )
                    )

        Ingredient.objects.bulk_create(ingredients, ignore_conflicts=True)

        self.stdout.write(
            self.style.SUCCESS(
                f'Загружено {len(ingredients)} ингредиентов из {file_path}'
            )
        )
