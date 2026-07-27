# security/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# إنشاء Router
router = DefaultRouter()

# تسجيل الـ ViewSets
router.register(r'users', views.UserViewSet, basename='security-user')
router.register(r'logs', views.SecurityLogViewSet, basename='security-log')
router.register(r'sessions', views.SessionViewSet, basename='security-session')
router.register(r'stats', views.SecurityStatsViewSet, basename='security-stats')
router.register(r'user-security', views.UserSecurityViewSet, basename='user-security')

# الروابط
urlpatterns = [
    path('', include(router.urls)),
]