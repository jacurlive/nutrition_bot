from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Meal
from .services import recalc_diary_totals


@receiver(post_save, sender=Meal)
def meal_saved(sender, instance: Meal, created, **kwargs):
    print("saved")
    recalc_diary_totals(instance.diary)


@receiver(post_delete, sender=Meal)
def meal_deleted(sender, instance: Meal, **kwargs):
    print("deleted")
    recalc_diary_totals(instance.diary)
