# settings_app/apps.py
from django.apps import AppConfig
from django.db.models.signals import post_migrate


def create_default_settings(sender, **kwargs):
    """إنشاء الإعدادات الافتراضية بعد الترحيل"""
    from .models import GeneralSettings
    
    if not GeneralSettings.objects.exists():
        GeneralSettings.objects.create()
        print("✅ Default General Settings created!")


class SettingsAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'settings_app'
    verbose_name = 'Settings Management'
    
    def ready(self):
        import settings_app.signals
        
        # ✅ إنشاء الإعدادات الافتراضية بعد الترحيل
        post_migrate.connect(create_default_settings, sender=self)
        
        print("✅ Settings signals loaded!")