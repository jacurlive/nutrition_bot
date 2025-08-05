from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator
from django.utils import timezone

from decimal import Decimal


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)

    class Meta:
        abstract = True


class Gender(models.TextChoices):
    MALE = "male", "Male"
    FEMALE = "female", "Female"


class Goal(models.TextChoices):
    LOSE = "lose", "Lose Weight"
    GAIN = "gain", "Gain Weight"
    MAINTAIN = "maintain", "Maintain"


class Language(models.TextChoices):
    RU = "ru", "Русский"
    EN = "en", "English"
    UZ = "uz", "O'zbekcha"


class AppUser(TimeStampedModel):
    telegram_id = models.BigIntegerField(unique=True, db_index=True)
    name = models.CharField(max_length=255, blank=True)
    gender = models.CharField(max_length=6, choices=Gender.choices, blank=True)
    age = models.PositiveIntegerField(null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(120)])
    height_cm = models.PositiveIntegerField(null=True, blank=True, validators=[MinValueValidator(50), MaxValueValidator(250)])
    weight_kg = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True,
                                    validators=[MinValueValidator(Decimal("20.0")), MaxValueValidator(Decimal("400.0"))])
    goal = models.CharField(max_length=10, choices=Goal.choices, default=Goal.MAINTAIN)
    language = models.CharField(max_length=2, choices=Language.choices, default=Language.RU)


    calorie_target = models.PositiveIntegerField(null=True, blank=True)
    protein_target_g = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    fat_target_g = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    carb_target_g = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)

    morning_summary_enabled = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.telegram_id} ({self.name or '-'})"


class Diary(TimeStampedModel):
    user = models.ForeignKey(AppUser, on_delete=models.CASCADE, related_name='diaries')
    date = models.DateField(db_index=True, default=timezone.localdate)

    total_calories = models.DecimalField(max_digits=9, decimal_places=2, default=0)
    total_protein = models.DecimalField(max_digits=9, decimal_places=2, default=0)
    total_fat = models.DecimalField(max_digits=9, decimal_places=2, default=0)
    total_carbs = models.DecimalField(max_digits=9, decimal_places=2, default=0)

    class Meta:
        unique_together = ('user', 'date')
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f"Diary(user-{self.user.telegram_id}, date={self.date})"


class Meal(TimeStampedModel):
    diary = models.ForeignKey(Diary, on_delete=models.CASCADE, related_name='meals')

    food_name = models.CharField(max_length=255)
    grams = models.PositiveIntegerField(validators=[MinValueValidator(1)])

    calories = models.DecimalField(max_digits=9, decimal_places=2)
    protein = models.DecimalField(max_digits=9, decimal_places=2)
    fat = models.DecimalField(max_digits=9, decimal_places=2)
    carbs = models.DecimalField(max_digits=9, decimal_places=2)

    image_url = models.CharField(max_length=300, null=True, blank=True)
    ai_raw_json = models.CharField(max_length=400, null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.food_name} ({self.grams} g)"
