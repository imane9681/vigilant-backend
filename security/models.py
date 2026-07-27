# security/models.py
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class SecurityLog(models.Model):
    """سجل الأحداث الأمنية"""
    
    SEVERITY_CHOICES = [
        ('critical', 'Critical'),
        ('warning', 'Warning'),
        ('info', 'Info'),
    ]
    
    EVENT_TYPES = [
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('failed_login', 'Failed Login'),
        ('password_change', 'Password Change'),
        ('password_reset', 'Password Reset'),
        ('2fa_enabled', '2FA Enabled'),
        ('2fa_disabled', '2FA Disabled'),
        ('account_locked', 'Account Locked'),
        ('account_unlocked', 'Account Unlocked'),
        ('session_created', 'Session Created'),
        ('session_terminated', 'Session Terminated'),
        ('permission_change', 'Permission Change'),
        ('user_created', 'User Created'),
        ('user_deleted', 'User Deleted'),
        ('user_updated', 'User Updated'),
    ]
    
    user = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='security_logs'
    )
    event_type = models.CharField(max_length=30, choices=EVENT_TYPES)
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default='info')
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, null=True)
    location = models.CharField(max_length=200, blank=True, null=True)
    details = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Security Log'
        verbose_name_plural = 'Security Logs'
    
    def __str__(self):
        return f"{self.get_event_type_display()} - {self.user} - {self.created_at}"

    @classmethod
    def cleanup_old_logs(cls, days=30):
        """
        حذف السجلات الأقدم من عدد محدد من الأيام
        """
        cutoff = timezone.now() - timezone.timedelta(days=days)
        old_logs = cls.objects.filter(created_at__lt=cutoff)
        count = old_logs.count()
        old_logs.delete()
        return count


class Session(models.Model):
    """جلسات المستخدمين النشطة"""
    
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        related_name='sessions'
    )
    session_key = models.CharField(max_length=100, unique=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    device_type = models.CharField(max_length=50, default='Unknown')
    location = models.CharField(max_length=200, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    last_activity = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    
    class Meta:
        ordering = ['-last_activity']
    
    def __str__(self):
        return f"{self.user.username} - {self.device_type} - {self.ip_address}"
    
    # ✅ ✅ ✅ دوال التنظيف الجديدة
    @classmethod
    def cleanup_expired(cls):
        """حذف الجلسات المنتهية تلقائياً"""
        expired = cls.objects.filter(expires_at__lt=timezone.now())
        count = expired.count()
        expired.delete()
        return count
    
    @classmethod
    def cleanup_inactive(cls, days=7):
        """حذف الجلسات غير النشطة منذ أكثر من X أيام"""
        cutoff = timezone.now() - timezone.timedelta(days=days)
        inactive = cls.objects.filter(
            is_active=False,
            last_activity__lt=cutoff
        )
        count = inactive.count()
        inactive.delete()
        return count


class SecurityStats(models.Model):
    """إحصائيات الأمان (يتم تحديثها تلقائياً)"""
    
    total_users = models.IntegerField(default=0)
    active_users = models.IntegerField(default=0)
    locked_users = models.IntegerField(default=0)
    admin_users = models.IntegerField(default=0)
    two_factor_enabled = models.IntegerField(default=0)
    strong_passwords = models.IntegerField(default=0)
    secure_sessions = models.IntegerField(default=0)
    active_sessions = models.IntegerField(default=0)
    failed_logins_today = models.IntegerField(default=0)
    failed_logins_week = models.IntegerField(default=0)
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Security Stats'
        verbose_name_plural = 'Security Stats'
    
    def __str__(self):
        return f"Stats - {self.last_updated}"


class UserSecurity(models.Model):
    """إعدادات الأمان لكل مستخدم"""
    
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name='security'
    )
    two_factor_enabled = models.BooleanField(default=False)
    has_strong_password = models.BooleanField(default=False)
    secure_session = models.BooleanField(default=False)
    last_password_change = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username} - 2FA: {self.two_factor_enabled}"
    
    class Meta:
        verbose_name = 'User Security'
        verbose_name_plural = 'User Securities'