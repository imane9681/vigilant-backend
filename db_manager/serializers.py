# database/serializers.py
from rest_framework import serializers
from .models import DatabaseBackup, DatabaseQueryLog, DatabaseTableInfo

class DatabaseBackupSerializer(serializers.ModelSerializer):
    size_display = serializers.CharField(read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True, default='System')
    
    class Meta:
        model = DatabaseBackup
        fields = [
            'id', 'name', 'type', 'size', 'size_display', 'status',
            'file_path', 'created_by', 'created_by_name',
            'created_at', 'completed_at'
        ]
        read_only_fields = ['id', 'created_at']

class DatabaseQueryLogSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.username', read_only=True, default='Anonymous')
    
    class Meta:
        model = DatabaseQueryLog
        fields = [
            'id', 'user', 'user_name', 'query', 'execution_time',
            'rows_affected', 'status', 'error_message', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

class DatabaseTableInfoSerializer(serializers.ModelSerializer):
    size_display = serializers.CharField(read_only=True)
    total_size = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = DatabaseTableInfo
        fields = [
            'id', 'table_name', 'row_count', 'data_size', 'index_size',
            'total_size', 'size_display', 'engine', 'collation',
            'last_updated'
        ]