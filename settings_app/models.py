# settings_app/models.py
from django.db import models
from django.contrib.auth.models import User


class GeneralSettings(models.Model):
    """الإعدادات العامة للنظام"""
    
    site_name = models.CharField(max_length=100, default='Vigilant Admin')
    site_description = models.TextField(default='Admin Dashboard for Vigilant', blank=True)
    admin_email = models.EmailField(default='admin@vigilant.com')
    
    timezone = models.CharField(max_length=50, default='UTC+3')
    date_format = models.CharField(max_length=20, default='YYYY-MM-DD')
    time_format = models.CharField(max_length=10, default='24h')
    language = models.CharField(max_length=10, default='en')
    
    maintenance_mode = models.BooleanField(default=False)
    debug_mode = models.BooleanField(default=False)
    
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        verbose_name = 'General Settings'
        verbose_name_plural = 'General Settings'
    
    def __str__(self):
        return f"General Settings - {self.updated_at}"


class NotificationSettings(models.Model):
    """إعدادات الإشعارات"""
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='notification_settings')
    
    email_notifications = models.BooleanField(default=True)
    push_notifications = models.BooleanField(default=True)
    desktop_notifications = models.BooleanField(default=False)
    
    order_alerts = models.BooleanField(default=True)
    stock_alerts = models.BooleanField(default=True)
    customer_alerts = models.BooleanField(default=False)
    system_alerts = models.BooleanField(default=True)
    marketing_emails = models.BooleanField(default=False)
    
    daily_summary = models.BooleanField(default=True)
    weekly_report = models.BooleanField(default=True)
    
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Notification Settings'
        verbose_name_plural = 'Notification Settings'
    
    def __str__(self):
        return f"Notification Settings - {self.user.username}"


class SecuritySettings(models.Model):
    """إعدادات الأمان"""
    
    SESSION_CONTROL_CHOICES = [
        ('strict', 'Strict - Single session only'),
        ('moderate', 'Moderate - Limited sessions'),
        ('loose', 'Loose - Multiple sessions allowed'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='security_settings')
    
    two_factor_auth = models.BooleanField(default=False)
    session_timeout = models.IntegerField(default=30)  # minutes
    max_login_attempts = models.IntegerField(default=5)
    password_expiry = models.IntegerField(default=90)  # days
    require_strong_password = models.BooleanField(default=True)
    ip_whitelisting = models.BooleanField(default=False)
    login_notifications = models.BooleanField(default=True)
    allow_multiple_sessions = models.BooleanField(default=False)
    session_control = models.CharField(max_length=20, choices=SESSION_CONTROL_CHOICES, default='strict')
    
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Security Settings'
        verbose_name_plural = 'Security Settings'
    
    def __str__(self):
        return f"Security Settings - {self.user.username}"