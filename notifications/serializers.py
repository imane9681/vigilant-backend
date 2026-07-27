# notifications/serializers.py
from rest_framework import serializers
from .models import Notification

class NotificationSerializer(serializers.ModelSerializer):
    time_ago = serializers.CharField(read_only=True)
    
    class Meta:
        model = Notification
        fields = ['id', 'user', 'title', 'message', 'type', 'icon', 'color', 
                  'link', 'is_read', 'created_at', 'time_ago']
        read_only_fields = ['id', 'user', 'created_at', 'time_ago']