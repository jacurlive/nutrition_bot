import os

from rest_framework import generics, viewsets
from rest_framework.permissions import BasePermission
from rest_framework.views import APIView
from rest_framework.response import Response

from django.utils.timezone import now
from datetime import timedelta

from dotenv import load_dotenv

from .models import AppUser, Diary, Meal
from .serializers import AppUserSerializer, DiarySerializer, MealSerializer
from .services import recalc_diary_totals


load_dotenv()


class CustomPermission(BasePermission):
    def has_permission(self, request, view):
        token = request.headers.get('Auth')
        bot_token = os.environ['BOT_TOKEN']
        return bot_token == token


class AppUserViewSet(viewsets.ModelViewSet):
    queryset = AppUser.objects.all()
    serializer_class = AppUserSerializer
    permission_classes = [CustomPermission]


class AppUserDetailByTelegramID(generics.RetrieveUpdateDestroyAPIView):
    queryset = AppUser.objects.all()
    serializer_class = AppUserSerializer
    permission_classes = [CustomPermission]
    lookup_field = 'telegram_id'


class DiaryViewSet(viewsets.ModelViewSet):
    queryset = Diary.objects.all()
    serializer_class = DiarySerializer
    permission_classes = [CustomPermission]


class DiaryViewByDate(generics.ListAPIView):
    queryset = Diary
    serializer_class = DiarySerializer

    def get_queryset(self):
        user_id = self.kwargs['user_id']
        year = int(self.kwargs['year'])
        month = int(self.kwargs['month'])
        day = int(self.kwargs['day'])
        
        diaries = Diary.objects.filter(
            user=user_id, date__year=year, date__month=month, date__day=day
        )

        for diary in diaries:
            recalc_diary_totals(diary)

        return diaries


class MealViewSet(viewsets.ModelViewSet):
    queryset = Meal.objects.all()
    serializer_class = MealSerializer
    permission_classes = [CustomPermission]


class UserStatsAPIView(APIView):
    permission_classes = [CustomPermission]

    def get(self, request):
        total_users = AppUser.objects.count()
        active_7_days = Meal.objects.filter(created_at__gte=now() - timedelta(days=7)).values("diary__user").distinct().count()
        active_1_days = Meal.objects.filter(created_at__gte=now() - timedelta(days=1)).values("diary__user").distinct().count()  

        return Response({
            "total_users": total_users,
            "active_7_days": active_7_days,
            "active_1_days": active_1_days
        })
    

class UserListByMorningReminderAPIView(generics.ListAPIView):
    queryset = AppUser.objects.filter(morning_summary_enabled=True)
    serializer_class = AppUserSerializer
    permission_classes = [CustomPermission]
