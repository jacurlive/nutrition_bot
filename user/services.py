from decimal import Decimal
from django.db.models import Sum
from .models import Diary


def recalc_diary_totals(diary: Diary):
    print("Service triggered")
    agg = diary.meals.aggregate(
        calories=Sum('calories'),
        protein=Sum('protein'),
        fat=Sum('fat'),
        carbs=Sum('carbs')
    )
    diary.total_calories = agg['calories'] or Decimal('0.00')
    diary.total_protein = agg['protein'] or Decimal('0.00')
    diary.total_fat = agg['fat'] or Decimal('0.00')
    diary.total_carbs = agg['carbs'] or Decimal('0.00')
    diary.save(update_fields=["total_calories", "total_protein", "total_fat", "total_carbs", "updated_at"])
