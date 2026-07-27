# security/signals.py
from django.db.models.signals import post_save, post_delete
from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.utils import timezone
from django.conf import settings
from .models import SecurityLog, Session, SecurityStats, UserSecurity


@receiver(post_save, sender=User)
def create_user_security(sender, instance, created, **kwargs):
    """إنشاء إعدادات أمان للمستخدم الجديد"""
    if created:
        UserSecurity.objects.create(user=instance)
        print(f"✅ UserSecurity created for {instance.username}")


@receiver(post_save, sender=User)
def log_user_creation(sender, instance, created, **kwargs):
    """تسجيل إنشاء مستخدم جديد"""
    if created:
        SecurityLog.objects.create(
            user=instance,
            event_type='user_created',
            severity='info',
            details={'new_user': instance.username}
        )
        print(f"✅ User creation logged for {instance.username}")


@receiver(post_delete, sender=User)
def log_user_deletion(sender, instance, **kwargs):
    """تسجيل حذف مستخدم"""
    SecurityLog.objects.create(
        user=None,
        event_type='user_deleted',
        severity='warning',
        details={'deleted_user': instance.username}
    )
    print(f"✅ User deletion logged for {instance.username}")


# ============================================================
# ✅ الحل الاحترافي: إدارة الجلسات الذكية
# ============================================================

@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    """
    ✅ تسجيل دخول المستخدم مع إدارة ذكية للجلسات
    ✅ تنظيف تلقائي للجلسات المنتهية وغير النشطة
    ✅ تحديد عدد الجلسات المسموح بها لكل مستخدم
    """
    
    print(f"🔐 User logged in: {user.username}")
    
    # ============================================================
    # 1️⃣ تنظيف الجلسات المنتهية تلقائياً
    # ============================================================
    expired_count = Session.cleanup_expired()
    if expired_count > 0:
        print(f"🧹 Cleaned up {expired_count} expired session(s)")
    
    # ============================================================
    # 2️⃣ تنظيف الجلسات غير النشطة القديمة
    # ============================================================
    days = getattr(settings, 'INACTIVE_SESSION_RETENTION_DAYS', 7)
    inactive_count = Session.cleanup_inactive(days=days)
    if inactive_count > 0:
        print(f"🧹 Cleaned up {inactive_count} inactive session(s)")
    
    # ============================================================
    # 3️⃣ إنهاء الجلسات القديمة للمستخدم الحالي
    # ============================================================
    old_sessions = Session.objects.filter(user=user, is_active=True)
    old_count = old_sessions.count()
    
    # ✅ إذا كان هناك أكثر من العدد المسموح به
    max_allowed = getattr(settings, 'MAX_ACTIVE_SESSIONS_PER_USER', 1)
    if old_count >= max_allowed:
        # احتفظ بأحدث جلسة فقط وأنهِ الباقي
        latest_session = old_sessions.order_by('-created_at').first()
        sessions_to_terminate = old_sessions.exclude(id=latest_session.id)
        terminated_count = sessions_to_terminate.count()
        sessions_to_terminate.update(is_active=False)
        print(f"🔄 Terminated {terminated_count} old session(s) for {user.username}")
        
        if terminated_count > 0:
            SecurityLog.objects.create(
                user=user,
                event_type='session_terminated',
                severity='info',
                ip_address=request.META.get('REMOTE_ADDR', '127.0.0.1'),
                details={
                    'terminated_sessions': terminated_count,
                    'reason': 'max_sessions_exceeded',
                    'max_allowed': max_allowed
                }
            )
    
    # ============================================================
    # 4️⃣ التأكد من وجود session_key
    # ============================================================
    session_key = request.session.session_key
    if not session_key:
        request.session.create()
        session_key = request.session.session_key
        print(f"🔄 Session created manually for {user.username}")
    
    # ============================================================
    # 5️⃣ إنشاء جلسة جديدة
    # ============================================================
    if session_key:
        session = Session.objects.create(
            user=user,
            session_key=session_key,
            ip_address=request.META.get('REMOTE_ADDR', '127.0.0.1'),
            user_agent=request.META.get('HTTP_USER_AGENT', 'Unknown'),
            device_type=_get_device_type(request.META.get('HTTP_USER_AGENT', '')),
            expires_at=timezone.now() + timezone.timedelta(days=7),
            is_active=True
        )
        print(f"✅ New session created for {user.username} (ID: {session.id})")
        
        SecurityLog.objects.create(
            user=user,
            event_type='session_created',
            severity='info',
            ip_address=request.META.get('REMOTE_ADDR', '127.0.0.1'),
            details={
                'session_id': session.id,
                'device_type': session.device_type
            }
        )
    
    # ============================================================
    # 6️⃣ تحديث إحصائيات الأمان
    # ============================================================
    try:
        stats = SecurityStats.objects.first()
        if stats:
            stats.active_sessions = Session.objects.filter(is_active=True).count()
            stats.save()
            print(f"📊 Updated active sessions count: {stats.active_sessions}")
    except Exception as e:
        print(f"⚠️ Could not update stats: {e}")


@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    """تسجيل خروج المستخدم وإنهاء جلساته"""
    if user:
        print(f"🔐 User logged out: {user.username}")
        
        SecurityLog.objects.create(
            user=user,
            event_type='logout',
            severity='info',
            ip_address=request.META.get('REMOTE_ADDR', '127.0.0.1'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        session_key = request.session.session_key
        if session_key:
            updated = Session.objects.filter(session_key=session_key, user=user).update(is_active=False)
            print(f"✅ Session terminated for {user.username} (updated: {updated})")
        
        try:
            stats = SecurityStats.objects.first()
            if stats:
                stats.active_sessions = Session.objects.filter(is_active=True).count()
                stats.save()
        except Exception as e:
            print(f"⚠️ Could not update stats: {e}")


@receiver(user_login_failed)
def log_failed_login(sender, credentials, request, **kwargs):
    """تسجيل محاولة دخول فاشلة"""
    username = credentials.get('username', 'unknown')
    print(f"❌ Failed login attempt: {username}")
    
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        user = None
    
    SecurityLog.objects.create(
        user=user,
        event_type='failed_login',
        severity='warning',
        ip_address=request.META.get('REMOTE_ADDR', '127.0.0.1'),
        user_agent=request.META.get('HTTP_USER_AGENT', ''),
        details={'username': username, 'failed': True}
    )


def _get_device_type(user_agent):
    """تحديد نوع الجهاز من User Agent"""
    user_agent = user_agent.lower()
    
    if 'mobile' in user_agent or 'android' in user_agent or 'iphone' in user_agent:
        return 'Mobile'
    elif 'tablet' in user_agent or 'ipad' in user_agent:
        return 'Tablet'
    else:
        return 'Desktop'