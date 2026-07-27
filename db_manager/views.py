# db_manager/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.conf import settings
from django.db import connection
from django.db import models
from django.utils import timezone
from django.http import FileResponse
from .models import DatabaseBackup, DatabaseQueryLog, DatabaseTableInfo
from .serializers import (
    DatabaseBackupSerializer, 
    DatabaseQueryLogSerializer, 
    DatabaseTableInfoSerializer
)
from .utils import get_database_stats, get_table_details
import os
import shutil
from datetime import datetime


class DatabaseViewSet(viewsets.GenericViewSet):
    """ViewSet لإدارة قاعدة البيانات"""
    
    permission_classes = [AllowAny]
    
    # ✅ ✅ ✅ مهم جداً - يمنع خطأ AssertionError
    queryset = DatabaseTableInfo.objects.none()
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """الحصول على إحصائيات قاعدة البيانات"""
        try:
            stats = get_database_stats()
            return Response(stats)
        except Exception as e:
            print(f"❌ Error in stats: {str(e)}")
            import traceback
            traceback.print_exc()
            return Response(
                {'error': str(e), 'detail': traceback.format_exc()},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def tables(self, request):
        """الحصول على قائمة الجداول"""
        try:
            tables = DatabaseTableInfo.objects.all()
            serializer = DatabaseTableInfoSerializer(tables, many=True)
            return Response(serializer.data)
        except Exception as e:
            print(f"❌ Error in tables: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def table_details(self, request):
        """✅ الحصول على تفاصيل جدول معين"""
        try:
            table_name = request.query_params.get('table_name')
            if not table_name:
                return Response(
                    {'error': 'table_name parameter is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            print(f"🔍 Fetching details for table: {table_name}")
            
            # ✅ جلب تفاصيل الجدول
            details = get_table_details(table_name)
            
            if details:
                print(f"✅ Table details found: {details.get('column_count', 0)} columns")
                return Response(details)
            
            return Response(
                {'error': f'Could not fetch details for table "{table_name}"'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            print(f"❌ Error in table_details: {str(e)}")
            import traceback
            traceback.print_exc()
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def backups(self, request):
        """الحصول على قائمة النسخ الاحتياطية"""
        try:
            backups = DatabaseBackup.objects.all()
            serializer = DatabaseBackupSerializer(backups, many=True)
            return Response(serializer.data)
        except Exception as e:
            print(f"❌ Error in backups: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'])
    def create_backup(self, request):
        """✅ إنشاء نسخة احتياطية جديدة"""
        try:
            # ✅ استخدام settings.DATABASE_BACKUP_PATH
            backup_path = settings.DATABASE_BACKUP_PATH
            
            # ✅ التأكد من وجود المجلد
            if not os.path.exists(backup_path):
                os.makedirs(backup_path)
                print(f"✅ Created backup directory: {backup_path}")
            
            # ✅ إنشاء اسم الملف
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_filename = f"backup_{timestamp}.sql"
            backup_filepath = os.path.join(backup_path, backup_filename)
            
            # ✅ إنشاء النسخة الاحتياطية
            db_path = settings.DATABASES['default']['NAME']
            
            if os.path.exists(db_path):
                # ✅ نسخ ملف قاعدة البيانات
                shutil.copy2(db_path, backup_filepath)
                backup_size = os.path.getsize(backup_filepath)
                
                # ✅ تسجيل في قاعدة البيانات
                backup = DatabaseBackup.objects.create(
                    name=f"Backup_{timestamp}",
                    type='full',
                    size=backup_size,
                    status='completed',
                    file_path=backup_filepath,
                    created_by=request.user if request.user.is_authenticated else None,
                    completed_at=timezone.now()
                )
                
                serializer = DatabaseBackupSerializer(backup)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            else:
                return Response(
                    {'error': 'Database file not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
        except Exception as e:
            print(f"❌ Error creating backup: {str(e)}")
            import traceback
            traceback.print_exc()
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['delete'])
    def delete_backup(self, request, pk=None):
        """✅ حذف نسخة احتياطية"""
        try:
            backup = DatabaseBackup.objects.get(pk=pk)
            file_path = backup.file_path
            
            # ✅ حذف الملف من النظام
            if file_path and os.path.exists(file_path):
                os.remove(file_path)
                print(f"✅ Deleted backup file: {file_path}")
            
            # ✅ حذف من قاعدة البيانات
            backup.delete()
            
            return Response(
                {'message': 'Backup deleted successfully'},
                status=status.HTTP_200_OK
            )
        except DatabaseBackup.DoesNotExist:
            return Response(
                {'error': 'Backup not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            print(f"❌ Error deleting backup: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'])
    def download_backup(self, request, pk=None):
        """✅ تحميل نسخة احتياطية"""
        try:
            backup = DatabaseBackup.objects.get(pk=pk)
            file_path = backup.file_path
            
            if not file_path or not os.path.exists(file_path):
                return Response(
                    {'error': 'Backup file not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # ✅ زيادة عدد التحميلات (إذا كان الحقل موجوداً)
            if hasattr(backup, 'download_count'):
                backup.download_count = (backup.download_count or 0) + 1
                backup.save()
            
            # ✅ إرجاع الملف
            response = FileResponse(
                open(file_path, 'rb'),
                as_attachment=True,
                filename=os.path.basename(file_path)
            )
            return response
            
        except DatabaseBackup.DoesNotExist:
            return Response(
                {'error': 'Backup not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            print(f"❌ Error downloading backup: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def restore_backup(self, request, pk=None):
        """✅ استعادة نسخة احتياطية"""
        try:
            backup = DatabaseBackup.objects.get(pk=pk)
            
            if backup.status != 'completed':
                return Response(
                    {'error': 'Backup is not completed'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # ✅ استخدام settings هنا أيضاً
            backup_path = settings.DATABASE_BACKUP_PATH
            db_path = settings.DATABASES['default']['NAME']
            
            # ✅ استعادة النسخة الاحتياطية
            if os.path.exists(backup.file_path):
                shutil.copy2(backup.file_path, db_path)
                
                # ✅ تحديث الحالة
                backup.status = 'restored'
                backup.save()
                
                return Response({
                    'message': f'Backup {backup.name} restored successfully',
                    'backup_id': backup.id
                })
            else:
                return Response(
                    {'error': 'Backup file not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
        except DatabaseBackup.DoesNotExist:
            return Response(
                {'error': 'Backup not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            print(f"❌ Error restoring backup: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def query_stats(self, request):
        """✅ الحصول على إحصائيات الاستعلامات"""
        try:
            # ✅ حساب الإحصائيات
            total_queries = DatabaseQueryLog.objects.count()
            slow_queries = DatabaseQueryLog.objects.filter(
                execution_time__gt=1000
            ).count()
            avg_time = DatabaseQueryLog.objects.aggregate(
                avg=models.Avg('execution_time')
            )['avg'] or 0
            
            # ✅ جلب أحدث 20 استعلام
            recent_queries = DatabaseQueryLog.objects.order_by('-created_at')[:20]
            serializer = DatabaseQueryLogSerializer(recent_queries, many=True)
            
            return Response({
                'total_queries': total_queries,
                'slow_queries': slow_queries,
                'avg_query_time': round(avg_time, 2),
                'recent_queries': serializer.data
            })
        except Exception as e:
            print(f"❌ Error in query_stats: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'])
    def execute_query(self, request):
        """✅ تنفيذ استعلام SQL مخصص"""
        try:
            query = request.data.get('query')
            if not query:
                return Response(
                    {'error': 'Query is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # ✅ تسجيل الوقت
            import time
            start_time = time.time()
            
            with connection.cursor() as cursor:
                cursor.execute(query)
                rows = cursor.fetchall()
                columns = [col[0] for col in cursor.description] if cursor.description else []
            
            execution_time = (time.time() - start_time) * 1000  # بالمللي ثانية
            
            # ✅ تسجيل في السجل
            DatabaseQueryLog.objects.create(
                user=request.user if request.user.is_authenticated else None,
                query=query,
                execution_time=execution_time,
                rows_affected=len(rows),
                status='success'
            )
            
            return Response({
                'columns': columns,
                'rows': rows,
                'row_count': len(rows),
                'execution_time': round(execution_time, 2)
            })
            
        except Exception as e:
            # ✅ تسجيل الخطأ
            DatabaseQueryLog.objects.create(
                user=request.user if request.user.is_authenticated else None,
                query=query if 'query' in locals() else '',
                status='error',
                error_message=str(e)
            )
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    # ✅ ✅ ✅ دالة حذف سجل استعلام معين
    @action(detail=True, methods=['delete'])
    def delete_query_log(self, request, pk=None):
        """✅ حذف سجل استعلام معين"""
        try:
            log = DatabaseQueryLog.objects.get(pk=pk)
            log.delete()
            return Response(
                {'message': 'Query log deleted successfully'},
                status=status.HTTP_200_OK
            )
        except DatabaseQueryLog.DoesNotExist:
            return Response(
                {'error': 'Query log not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            print(f"❌ Error deleting query log: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'])
    def clear_logs(self, request):
        """✅ مسح جميع سجلات الاستعلامات"""
        try:
            days = request.data.get('days', 30)
            try:
                days = int(days)
            except (ValueError, TypeError):
                days = 30
            
            # ✅ حذف السجلات الأقدم من عدد الأيام
            cutoff = timezone.now() - timezone.timedelta(days=days)
            deleted_count = DatabaseQueryLog.objects.filter(
                created_at__lt=cutoff
            ).delete()[0]
            
            return Response({
                'message': f'Deleted {deleted_count} logs older than {days} days',
                'deleted_count': deleted_count
            })
            
        except Exception as e:
            print(f"❌ Error clearing logs: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )