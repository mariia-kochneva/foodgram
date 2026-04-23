from io import BytesIO

from django.db.models import Sum
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from recipes.models import RecipeIngredient


def get_shopping_cart_ingredients(user):
    """Получить список ингредиентов для списка покупок пользователя."""
    return (
        RecipeIngredient.objects
        .filter(recipe__shopping_cart__user=user)
        .select_related('ingredient')
        .values(
            'ingredient__name',
            'ingredient__measurement_unit'
        )
        .annotate(total_amount=Sum('amount'))
        .order_by('ingredient__name')
    )


def generate_shopping_cart_pdf(user, ingredients):
    """Сгенерировать PDF со списком покупок."""
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    font_name = 'Helvetica'
    try:
        pdfmetrics.registerFont(TTFont('DejaVu', 'DejaVuSans.ttf'))
        font_name = 'DejaVu'
    except Exception:
        pass

    # Заголовок
    p.setFont(font_name, 16)
    p.drawString(50, height - 50, 'Список покупок')
    p.setFont(font_name, 12)
    p.drawString(50, height - 70, f'Пользователь: {user.username}')

    # Ингредиенты
    y = height - 100
    p.setFont(font_name, 10)

    if not ingredients:
        p.drawString(50, y, 'Список покупок пуст.')
    else:
        for item in ingredients:
            line = (
                f"{item['ingredient__name']} "
                f"({item['ingredient__measurement_unit']}) — "
                f"{item['total_amount']}"
            )
            p.drawString(50, y, line)
            y -= 15
            if y < 50:
                p.showPage()
                y = height - 50
                p.setFont(font_name, 10)

    p.save()
    buffer.seek(0)
    return buffer
