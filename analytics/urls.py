# analytics/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard_metrics, name='dashboard_metrics'),
    path('sales/', views.sales_data, name='sales_data'),
    path('revenue/', views.revenue_data, name='revenue_data'),
]