# products/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProductViewSet, CategoryViewSet  # ✅ إضافة الـ import هنا

# Create router for ViewSets
router = DefaultRouter()
router.register(r'products', ProductViewSet, basename='product')
router.register(r'categories', CategoryViewSet, basename='category')  # ✅ إضافة

# URL patterns
urlpatterns = [
    path('', include(router.urls)),
]