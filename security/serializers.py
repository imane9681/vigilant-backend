# security/serializers.py
from rest_framework import serializers
from django.contrib.auth.models import User
from .models import SecurityLog, Session, SecurityStats, UserSecurity


class UserSerializer(serializers.ModelSerializer):
    """Serializer للمستخدمين"""
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'is_active', 'is_staff', 'is_superuser', 'last_login', 'date_joined']
        read_only_fields = ['id', 'last_login', 'date_joined']


class UserSecuritySerializer(serializers.ModelSerializer):
    """Serializer لإعدادات أمان المستخدم"""
    
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.CharField(source='user.email', read_only=True)
    
    class Meta:
        model = UserSecurity
        fields = ['id', 'user', 'username', 'email', 'two_factor_enabled', 
                  'has_strong_password', 'secure_session', 'last_password_change', 
                  'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class SecurityLogSerializer(serializers.ModelSerializer):
    """Serializer لسجلات الأمان"""
    
    user_name = serializers.CharField(source='user.username', read_only=True, default='Unknown')
    user_email = serializers.CharField(source='user.email', read_only=True, default='')
    event_display = serializers.CharField(source='get_event_type_display', read_only=True)
    severity_display = serializers.CharField(source='get_severity_display', read_only=True)
    time_ago = serializers.SerializerMethodField()
    
    class Meta:
        model = SecurityLog
        fields = [
            'id', 'user', 'user_name', 'user_email',
            'event_type', 'event_display',
            'severity', 'severity_display',
            'ip_address', 'user_agent', 'location',
            'details', 'time_ago', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_time_ago(self, obj):
        from django.utils import timezone
        diff = timezone.now() - obj.created_at
        days = diff.days
        hours = diff.seconds // 3600
        minutes = (diff.seconds // 60) % 60
        
        if days > 0:
            return f"{days}d ago"
        elif hours > 0:
            return f"{hours}h ago"
        elif minutes > 0:
            return f"{minutes}m ago"
        return "Just now"


class SessionSerializer(serializers.ModelSerializer):
    """Serializer للجلسات"""
    
    user_name = serializers.CharField(source='user.username', read_only=True)
    is_expired = serializers.SerializerMethodField()
    
    class Meta:
        model = Session
        fields = [
            'id', 'user', 'user_name',
            'session_key', 'ip_address', 'user_agent',
            'device_type', 'location', 'is_active',
            'is_expired', 'last_activity', 'created_at', 'expires_at'
        ]
        read_only_fields = ['id', 'created_at', 'last_activity']
    
    def get_is_expired(self, obj):
        from django.utils import timezone
        return timezone.now() > obj.expires_at


class SecurityStatsSerializer(serializers.ModelSerializer):
    """Serializer لإحصائيات الأمان"""
    
    class Meta:
        model = SecurityStats
        fields = '__all__'
        read_only_fields = ['id', 'last_updated']