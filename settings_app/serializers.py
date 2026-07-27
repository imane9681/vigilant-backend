# settings_app/serializers.py
from rest_framework import serializers
from .models import GeneralSettings, NotificationSettings, SecuritySettings


class GeneralSettingsSerializer(serializers.ModelSerializer):
    """Serializer للإعدادات العامة"""
    
    class Meta:
        model = GeneralSettings
        fields = [
            'id', 'site_name', 'site_description', 'admin_email',
            'timezone', 'date_format', 'time_format', 'language',
            'maintenance_mode', 'debug_mode',
            'updated_at', 'updated_by'
        ]
        read_only_fields = ['id', 'updated_at']
        # ✅ اجعل updated_by غير مطلوب في التحديث
        extra_kwargs = {
            'updated_by': {'required': False, 'allow_null': True}
        }


class NotificationSettingsSerializer(serializers.ModelSerializer):
    """Serializer لإعدادات الإشعارات"""
    
    username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = NotificationSettings
        fields = [
            'id', 'user', 'username',
            'email_notifications', 'push_notifications', 'desktop_notifications',
            'order_alerts', 'stock_alerts', 'customer_alerts',
            'system_alerts', 'marketing_emails',
            'daily_summary', 'weekly_report',
            'updated_at'
        ]
        read_only_fields = ['id', 'user', 'username', 'updated_at']


class SecuritySettingsSerializer(serializers.ModelSerializer):
    """Serializer لإعدادات الأمان"""
    
    username = serializers.CharField(source='user.username', read_only=True)
    session_control_display = serializers.CharField(source='get_session_control_display', read_only=True)
    
    class Meta:
        model = SecuritySettings
        fields = [
            'id', 'user', 'username',
            'two_factor_auth', 'session_timeout', 'max_login_attempts',
            'password_expiry', 'require_strong_password', 'ip_whitelisting',
            'login_notifications', 'allow_multiple_sessions',
            'session_control', 'session_control_display',
            'updated_at'
        ]
        read_only_fields = ['id', 'user', 'username', 'updated_at']