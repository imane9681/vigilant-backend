# notifications/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# ✅ إنشاء Router
router = DefaultRouter()

# ✅ تسجيل الـ ViewSet بدون بادئة إضافية (استخدم سلسلة فارغة)
router.register(r'', views.NotificationViewSet, basename='notification')

# ✅ الروابط
urlpatterns = [
    path('', include(router.urls)),
]