# settings_app/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import NotificationSettings, SecuritySettings


@receiver(post_save, sender=User)
def create_user_settings(sender, instance, created, **kwargs):
    """
    إنشاء إعدادات تلقائية للمستخدم الجديد
    """
    if created:
        # ✅ إنشاء إعدادات الإشعارات للمستخدم الجديد
        NotificationSettings.objects.create(user=instance)
        print(f"✅ Notification settings created for {instance.username}")
        
        # ✅ إنشاء إعدادات الأمان للمستخدم الجديد
        SecuritySettings.objects.create(user=instance)
        print(f"✅ Security settings created for {instance.username}")