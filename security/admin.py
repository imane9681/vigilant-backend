# security/admin.py
from django.contrib import admin
from .models import SecurityLog, Session, SecurityStats, UserSecurity


@admin.register(SecurityLog)
class SecurityLogAdmin(admin.ModelAdmin):
    list_display = ['id', 'event_type', 'severity', 'user', 'ip_address', 'created_at']
    list_filter = ['event_type', 'severity', 'created_at']
    search_fields = ['user__username', 'user__email', 'ip_address', 'location']
    readonly_fields = ['created_at']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Event Information', {
            'fields': ('event_type', 'severity', 'user')
        }),
        ('Location Information', {
            'fields': ('ip_address', 'user_agent', 'location')
        }),
        ('Details', {
            'fields': ('details', 'created_at')
        }),
    )


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'device_type', 'ip_address', 'is_active', 'last_activity', 'expires_at']
    list_filter = ['is_active', 'device_type', 'created_at']
    search_fields = ['user__username', 'user__email', 'ip_address', 'location']
    readonly_fields = ['created_at', 'last_activity']
    ordering = ['-last_activity']


@admin.register(SecurityStats)
class SecurityStatsAdmin(admin.ModelAdmin):
    list_display = ['id', 'total_users', 'active_users', 'locked_users', 'active_sessions', 'last_updated']
    readonly_fields = ['id', 'last_updated']


@admin.register(UserSecurity)
class UserSecurityAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'two_factor_enabled', 'has_strong_password', 'secure_session', 'updated_at']
    list_filter = ['two_factor_enabled', 'has_strong_password', 'secure_session']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['created_at', 'updated_at']