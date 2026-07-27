# database/models.py
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class DatabaseBackup(models.Model):
    """نموذج النسخ الاحتياطية"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    TYPE_CHOICES = [
        ('full', 'Full Backup'),
        ('incremental', 'Incremental Backup'),
    ]
    
    name = models.CharField(max_length=200)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='full')
    size = models.BigIntegerField(default=0)  # الحجم بالبايت
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    file_path = models.CharField(max_length=500, blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Database Backup'
        verbose_name_plural = 'Database Backups'
    
    def __str__(self):
        return f"{self.name} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"
    
    @property
    def size_display(self):
        """عرض الحجم بشكل مقروء"""
        if self.size < 1024:
            return f"{self.size} B"
        elif self.size < 1024 * 1024:
            return f"{self.size / 1024:.1f} KB"
        elif self.size < 1024 * 1024 * 1024:
            return f"{self.size / (1024 * 1024):.1f} MB"
        else:
            return f"{self.size / (1024 * 1024 * 1024):.2f} GB"


class DatabaseQueryLog(models.Model):
    """نموذج سجلات الاستعلامات"""
    
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    query = models.TextField()
    execution_time = models.FloatField(default=0)  # بالمللي ثانية
    rows_affected = models.IntegerField(default=0)
    status = models.CharField(max_length=20, default='success')
    error_message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Database Query Log'
        verbose_name_plural = 'Database Query Logs'
    
    def __str__(self):
        return f"{self.user} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"


class DatabaseTableInfo(models.Model):
    """نموذج معلومات الجداول (يتم تحديثه تلقائياً)"""
    
    table_name = models.CharField(max_length=100, unique=True)
    row_count = models.IntegerField(default=0)
    data_size = models.BigIntegerField(default=0)  # بالبايت
    index_size = models.BigIntegerField(default=0)  # بالبايت
    engine = models.CharField(max_length=50, default='InnoDB')
    collation = models.CharField(max_length=50, default='utf8mb4_unicode_ci')
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['table_name']
        verbose_name = 'Database Table Info'
        verbose_name_plural = 'Database Tables Info'
    
    def __str__(self):
        return self.table_name
    
    @property
    def total_size(self):
        """الحجم الإجمالي للجدول"""
        return self.data_size + self.index_size
    
    @property
    def size_display(self):
        """عرض الحجم بشكل مقروء"""
        total = self.total_size
        if total < 1024:
            return f"{total} B"
        elif total < 1024 * 1024:
            return f"{total / 1024:.1f} KB"
        elif total < 1024 * 1024 * 1024:
            return f"{total / (1024 * 1024):.1f} MB"
        else:
            return f"{total / (1024 * 1024 * 1024):.2f} GB"