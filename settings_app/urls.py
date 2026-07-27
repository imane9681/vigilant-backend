# settings_app/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# إنشاء Router
router = DefaultRouter()

# تسجيل الـ ViewSets
router.register(r'general', views.GeneralSettingsViewSet, basename='settings-general')
router.register(r'notifications', views.NotificationSettingsViewSet, basename='settings-notifications')
router.register(r'security', views.SecuritySettingsViewSet, basename='settings-security')

# الروابط
urlpatterns = [
    path('', include(router.urls)),
]