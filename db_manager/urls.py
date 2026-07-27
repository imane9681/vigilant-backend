# db_manager/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'', views.DatabaseViewSet, basename='database')

urlpatterns = [
    path('', include(router.urls)),
]