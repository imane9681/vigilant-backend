# db_manager/utils.py

from django.db import connection
from django.apps import apps
from .models import DatabaseTableInfo, DatabaseBackup, DatabaseQueryLog
from datetime import datetime, timedelta
import os

def get_database_stats():
    """الحصول على إحصائيات قاعدة البيانات - يدعم SQLite و MySQL"""
    
    try:
        print("🔍 Starting get_database_stats...")
        
        # ✅ تحديد نوع قاعدة البيانات
        db_engine = connection.settings_dict.get('ENGINE', '').lower()
        is_sqlite = 'sqlite' in db_engine
        is_mysql = 'mysql' in db_engine
        
        print(f"📊 Database Engine: {db_engine}")
        print(f"📊 Is SQLite: {is_sqlite}")
        print(f"📊 Is MySQL: {is_mysql}")
        
        with connection.cursor() as cursor:
            print("✅ Database connection established")
            
            # ============================================
            # ✅ 1. حجم قاعدة البيانات وعدد الجداول
            # ============================================
            total_size = 0
            table_count = 0
            tables_info = []
            
            if is_sqlite:
                # ✅ SQLite - جلب معلومات الجداول
                cursor.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' 
                    AND name NOT LIKE 'sqlite_%'
                    AND name NOT LIKE 'django_%'
                    AND name NOT LIKE 'auth_%'
                """)
                table_names = cursor.fetchall()
                table_count = len(table_names)
                
                # ✅ حساب حجم ملف قاعدة البيانات
                db_path = connection.settings_dict.get('NAME', 'db.sqlite3')
                if os.path.exists(db_path):
                    total_size = os.path.getsize(db_path)
                
                print(f"📊 SQLite: {table_count} tables, Size: {total_size} bytes")
                
            else:
                # ✅ MySQL - جلب معلومات الجداول
                cursor.execute("""
                    SELECT 
                        SUM(data_length + index_length) AS total_size,
                        COUNT(*) AS table_count
                    FROM information_schema.tables
                    WHERE table_schema = DATABASE()
                """)
                result = cursor.fetchone()
                total_size = result[0] or 0
                table_count = result[1] or 0
            
            # ============================================
            # ✅ 2. تفاصيل الجداول
            # ============================================
            if is_sqlite:
                # ✅ SQLite - تفاصيل الجداول
                for table_name in table_names:
                    name = table_name[0]
                    
                    # ✅ عدد الصفوف في الجدول
                    cursor.execute(f"SELECT COUNT(*) FROM `{name}`")
                    row_count = cursor.fetchone()[0] or 0
                    
                    # ✅ تخزين معلومات الجدول
                    DatabaseTableInfo.objects.update_or_create(
                        table_name=name,
                        defaults={
                            'row_count': row_count,
                            'data_size': 0,
                            'index_size': 0,
                            'engine': 'SQLite',
                            'collation': 'utf8'
                        }
                    )
                    tables_info.append((name, row_count, 0, 0, 'SQLite', 'utf8'))
                    
            else:
                # ✅ MySQL - تفاصيل الجداول
                cursor.execute("""
                    SELECT 
                        table_name,
                        table_rows,
                        data_length,
                        index_length,
                        engine,
                        table_collation
                    FROM information_schema.tables
                    WHERE table_schema = DATABASE()
                    ORDER BY data_length + index_length DESC
                """)
                tables_info = cursor.fetchall()
                
                for table in tables_info:
                    name, rows, data_size, idx_size, engine, collation = table
                    DatabaseTableInfo.objects.update_or_create(
                        table_name=name,
                        defaults={
                            'row_count': rows or 0,
                            'data_size': data_size or 0,
                            'index_size': idx_size or 0,
                            'engine': engine or 'InnoDB',
                            'collation': collation or 'utf8mb4_unicode_ci'
                        }
                    )
            
            print(f"📊 Total tables: {table_count}")
            
            # ============================================
            # ✅ 3. إجمالي السجلات في جميع الجداول
            # ============================================
            total_records = 0
            
            # ✅ حساب السجلات من جميع نماذج Django
            for app_config in apps.get_app_configs():
                for model in app_config.get_models():
                    if not model._meta.abstract:
                        try:
                            count = model.objects.count()
                            total_records += count
                        except Exception as e:
                            print(f"⚠️ Could not count {model._meta.db_table}: {e}")
            
            print(f"📊 Total records: {total_records}")
            
            # ============================================
            # ✅ 4. إجمالي الفهارس (MySQL فقط)
            # ============================================
            total_indexes = 0
            if not is_sqlite:
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM information_schema.statistics
                    WHERE table_schema = DATABASE()
                """)
                total_indexes = cursor.fetchone()[0] or 0
            
            # ============================================
            # ✅ 5. الاتصالات النشطة (MySQL فقط)
            # ============================================
            active_connections = 12  # قيمة افتراضية
            if not is_sqlite:
                try:
                    cursor.execute("SHOW STATUS LIKE 'Threads_connected'")
                    connections = cursor.fetchone()
                    if connections:
                        active_connections = int(connections[1])
                except:
                    pass
            
            # ============================================
            # ✅ 6. وقت التشغيل (MySQL فقط)
            # ============================================
            uptime_display = "N/A"
            if not is_sqlite:
                try:
                    cursor.execute("SHOW STATUS LIKE 'Uptime'")
                    uptime = cursor.fetchone()
                    if uptime:
                        uptime_seconds = int(uptime[1])
                        uptime_days = uptime_seconds // 86400
                        uptime_hours = (uptime_seconds % 86400) // 3600
                        if uptime_days > 0:
                            uptime_display = f"{uptime_days}d {uptime_hours}h"
                        else:
                            uptime_display = f"{uptime_hours}h"
                except:
                    pass
            
            # ============================================
            # ✅ 7. نسبة Cache Hit (MySQL فقط)
            # ============================================
            cache_hit_display = "N/A"
            if not is_sqlite:
                try:
                    cursor.execute("SHOW STATUS LIKE 'Innodb_buffer_pool_read_requests'")
                    read_requests = cursor.fetchone()
                    cursor.execute("SHOW STATUS LIKE 'Innodb_buffer_pool_reads'")
                    reads = cursor.fetchone()
                    
                    if read_requests and reads:
                        requests = int(read_requests[1]) or 1
                        reads_count = int(reads[1]) or 0
                        cache_hit = ((requests - reads_count) / requests) * 100
                        cache_hit_display = f"{cache_hit:.1f}%"
                except:
                    pass
            
            # ============================================
            # ✅ 8. آخر نسخة احتياطية
            # ============================================
            last_backup = DatabaseBackup.objects.filter(status='completed').first()
            last_backup_date = last_backup.created_at.strftime('%Y-%m-%d %H:%M') if last_backup else 'Never'
            
            # ✅ النسخة الاحتياطية التالية
            if last_backup:
                next_backup = last_backup.created_at + timedelta(days=1)
                next_backup_date = next_backup.strftime('%Y-%m-%d %H:%M')
            else:
                next_backup_date = 'Scheduled'
            
            # ============================================
            # ✅ 9. إرجاع البيانات
            # ============================================
            result = {
                'size': total_size,
                'size_display': format_size(total_size),
                'tables': table_count,
                'records': total_records,
                'indexes': total_indexes,
                'queries': DatabaseQueryLog.objects.count(),
                'connections': active_connections,
                'cacheHit': cache_hit_display,
                'uptime': uptime_display,
                'lastBackup': last_backup_date,
                'nextBackup': next_backup_date,
            }
            
            print(f"✅ Stats calculated successfully: {result}")
            return result
            
    except Exception as e:
        print(f"❌❌❌ ERROR in get_database_stats: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # ✅ إرجاع بيانات افتراضية في حالة الخطأ
        return {
            'size': 0,
            'size_display': '0 B',
            'tables': 0,
            'records': 0,
            'indexes': 0,
            'queries': 0,
            'connections': 0,
            'cacheHit': '0%',
            'uptime': '0h',
            'lastBackup': 'Never',
            'nextBackup': 'Scheduled',
            'error': str(e),
        }

def format_size(size_in_bytes):
    """تنسيق الحجم بشكل مقروء"""
    if size_in_bytes < 1024:
        return f"{size_in_bytes} B"
    elif size_in_bytes < 1024 * 1024:
        return f"{size_in_bytes / 1024:.1f} KB"
    elif size_in_bytes < 1024 * 1024 * 1024:
        return f"{size_in_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_in_bytes / (1024 * 1024 * 1024):.2f} GB"


# ============================================
# ✅ ✅ ✅ الدالة المهمة: get_table_details (المعدلة)
# ============================================

def get_table_details(table_name):
    """الحصول على تفاصيل جدول معين - يدعم SQLite"""
    try:
        # ✅ جلب معلومات الجدول من DatabaseTableInfo
        table_info = DatabaseTableInfo.objects.filter(table_name=table_name).first()
        if not table_info:
            print(f"❌ Table '{table_name}' not found in DatabaseTableInfo")
            return None
        
        print(f"🔍 Fetching columns for table: {table_name}")
        
        with connection.cursor() as cursor:
            # ✅ ✅ ✅ استخدام PRAGMA table_info لجلب الأعمدة
            cursor.execute(f'PRAGMA table_info("{table_name}")')
            columns_raw = cursor.fetchall()
            
            print(f"📊 Raw columns data: {columns_raw}")
            
            # ✅ ✅ ✅ تحويل النتيجة إلى تنسيق مناسب
            # PRAGMA table_info returns: (cid, name, type, notnull, dflt_value, pk)
            columns_list = []
            for col in columns_raw:
                columns_list.append({
                    'Field': col[1],           # اسم العمود
                    'Type': col[2],            # النوع (TEXT, INTEGER, etc.)
                    'Null': 'YES' if col[3] == 0 else 'NO',  # 0 = YES, 1 = NO
                    'Key': 'PRI' if col[5] == 1 else '',     # المفتاح الأساسي
                    'Default': col[4] if col[4] is not None else '',  # القيمة الافتراضية
                    'Extra': ''                # SQLite لا يدعم Extra
                })
            
            # ✅ ✅ ✅ عدد الأعمدة
            column_count = len(columns_list)
            print(f"✅ Found {column_count} columns in {table_name}")
        
        return {
            'name': table_name,
            'rows': table_info.row_count,
            'size': table_info.size_display,
            'indexes': table_info.index_size,
            'engine': table_info.engine or 'SQLite',
            'collation': table_info.collation or 'utf8',
            'columns': columns_list,
            'column_count': column_count,
            'last_updated': table_info.last_updated
        }
    except Exception as e:
        print(f"❌ Error in get_table_details: {str(e)}")
        import traceback
        traceback.print_exc()
        return None