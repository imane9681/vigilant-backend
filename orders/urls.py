# orders/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register('customers', views.CustomerViewSet)
router.register('', views.OrderViewSet)

urlpatterns = [
    path('', include(router.urls)),
]