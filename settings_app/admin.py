# settings_app/admin.py
from django.contrib import admin
from .models import GeneralSettings, NotificationSettings, SecuritySettings


@admin.register(GeneralSettings)
class GeneralSettingsAdmin(admin.ModelAdmin):
    list_display = ['id', 'site_name', 'admin_email', 'timezone', 'maintenance_mode', 'updated_at']
    list_filter = ['maintenance_mode', 'debug_mode', 'timezone']
    search_fields = ['site_name', 'admin_email']
    readonly_fields = ['updated_at']
    
    fieldsets = (
        ('Site Information', {
            'fields': ('site_name', 'site_description', 'admin_email')
        }),
        ('Regional Settings', {
            'fields': ('timezone', 'date_format', 'time_format', 'language')
        }),
        ('System Status', {
            'fields': ('maintenance_mode', 'debug_mode')
        }),
        ('Metadata', {
            'fields': ('updated_at', 'updated_by')
        }),
    )


@admin.register(NotificationSettings)
class NotificationSettingsAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'email_notifications', 'order_alerts', 'stock_alerts', 'updated_at']
    list_filter = ['email_notifications', 'push_notifications', 'desktop_notifications']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['updated_at']


@admin.register(SecuritySettings)
class SecuritySettingsAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'two_factor_auth', 'session_timeout', 'session_control', 'updated_at']
    list_filter = ['two_factor_auth', 'require_strong_password', 'ip_whitelisting']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['updated_at']