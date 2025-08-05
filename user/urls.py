from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import AppUserViewSet, DiaryViewSet, MealViewSet, AppUserDetailByTelegramID, DiaryViewByDate, UserStatsAPIView


router = DefaultRouter()
router.register(r'users', AppUserViewSet, basename='users')
router.register(r'diary', DiaryViewSet, basename='diary')
router.register(r'meal', MealViewSet, basename='meal')


urlpatterns = [
    path('', include(router.urls)),
    path('users/telegram/<int:telegram_id>', AppUserDetailByTelegramID.as_view()),
    path('diary/date/<int:user_id>/<str:year>/<str:month>/<str:day>', DiaryViewByDate.as_view()),
    path("stats/", UserStatsAPIView.as_view())
]
