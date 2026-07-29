# config/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve
from django.urls import re_path
from rest_framework.routers import DefaultRouter
from products.views import ProductViewSet, CategoryViewSet, PromotionViewSet, ReportViewSet

# إنشاء router رئيسي
router = DefaultRouter()
router.register(r'products', ProductViewSet, basename='product')
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'promotions', PromotionViewSet, basename='promotion')
router.register(r'reports', ReportViewSet, basename='report')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('accounts.urls')),
    path('api/analytics/', include('analytics.urls')),
    path('api/orders/', include('orders.urls')),
    path('api/notifications/', include('notifications.urls')), 
    path('api/security/', include('security.urls')),
    path('api/settings/', include('settings_app.urls')),
    path('api/database/', include('db_manager.urls')),  
    path('api/', include(router.urls)),  # ✅ جميع الـ APIs في router واحد
]

# ✅ ✅ ✅ خدمة ملفات media في جميع الحالات (حتى مع DEBUG=False)
urlpatterns += [
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
    re_path(r'^static/(?P<path>.*)$', serve, {'document_root': settings.STATIC_ROOT}),
]

# ✅ للتطوير المحلي فقط
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)