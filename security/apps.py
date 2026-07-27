# security/apps.py
from django.apps import AppConfig


class SecurityConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'security'
    verbose_name = 'Security Management'
    
    def ready(self):
        import security.signals
        print("✅ Security signals loaded!")