# security/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models import Count, Q
from datetime import timedelta
from django.conf import settings
from .models import SecurityLog, Session, SecurityStats, UserSecurity
from .serializers import (
    UserSerializer, SecurityLogSerializer, 
    SessionSerializer, SecurityStatsSerializer,
    UserSecuritySerializer
)


class UserViewSet(viewsets.ModelViewSet):
    """ViewSet للمستخدمين"""
    
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    
    @action(detail=True, methods=['post'])
    def lock(self, request, pk=None):
        """قفل حساب مستخدم"""
        user = self.get_object()
        user.is_active = False
        user.save()
        
        # ✅ تسجيل الحدث
        SecurityLog.objects.create(
            user=request.user,
            event_type='account_locked',
            severity='warning',
            ip_address=request.META.get('REMOTE_ADDR'),
            details={'locked_user': user.username}
        )
        
        # ✅ ✅ ✅ تحديث الإحصائيات
        self._update_stats()
        
        return Response({
            'status': f'User {user.username} locked',
            'user': user.username,
            'is_active': user.is_active
        })
    
    @action(detail=True, methods=['post'])
    def unlock(self, request, pk=None):
        """فتح حساب مستخدم"""
        user = self.get_object()
        user.is_active = True
        user.save()
        
        # ✅ تسجيل الحدث
        SecurityLog.objects.create(
            user=request.user,
            event_type='account_unlocked',
            severity='info',
            ip_address=request.META.get('REMOTE_ADDR'),
            details={'unlocked_user': user.username}
        )
        
        # ✅ ✅ ✅ تحديث الإحصائيات
        self._update_stats()
        
        return Response({
            'status': f'User {user.username} unlocked',
            'user': user.username,
            'is_active': user.is_active
        })
    
    def _update_stats(self):
        """تحديث إحصائيات الأمان"""
        try:
            stats, created = SecurityStats.objects.get_or_create(id=1)
            
            stats.total_users = User.objects.count()
            stats.active_users = User.objects.filter(is_active=True).count()
            stats.locked_users = User.objects.filter(is_active=False).count()
            stats.admin_users = User.objects.filter(is_superuser=True).count()
            
            stats.two_factor_enabled = UserSecurity.objects.filter(two_factor_enabled=True).count()
            stats.strong_passwords = UserSecurity.objects.filter(has_strong_password=True).count()
            stats.secure_sessions = UserSecurity.objects.filter(secure_session=True).count()
            
            stats.active_sessions = Session.objects.filter(is_active=True).count()
            
            stats.save()
            print(f"📊 Stats updated: active={stats.active_users}, locked={stats.locked_users}")
        except Exception as e:
            print(f"⚠️ Could not update stats: {e}")


class SecurityLogViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet لسجلات الأمان"""
    
    queryset = SecurityLog.objects.all()
    serializer_class = SecurityLogSerializer
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        event_type = self.request.query_params.get('event_type')
        if event_type:
            queryset = queryset.filter(event_type=event_type)
        
        severity = self.request.query_params.get('severity')
        if severity:
            queryset = queryset.filter(severity=severity)
        
        user_id = self.request.query_params.get('user_id')
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """إحصائيات سجلات الأمان"""
        today = timezone.now().date()
        week_ago = today - timedelta(days=7)
        
        total = SecurityLog.objects.count()
        today_count = SecurityLog.objects.filter(created_at__date=today).count()
        week_count = SecurityLog.objects.filter(created_at__date__gte=week_ago).count()
        
        by_severity = SecurityLog.objects.values('severity').annotate(count=Count('id'))
        by_event = SecurityLog.objects.values('event_type').annotate(count=Count('id'))[:10]
        
        return Response({
            'total': total,
            'today': today_count,
            'week': week_count,
            'by_severity': by_severity,
            'by_event': by_event,
        })

    @action(detail=False, methods=['post'])
    def cleanup(self, request):
        """
        تنظيف سجلات الأمان القديمة
        """
        days = request.data.get('days', 30)
    
        try:
           days = int(days)
           if days < 0:
                return Response(
                    {'error': 'Days cannot be negative'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except (ValueError, TypeError):
            return Response(
                {'error': 'Days must be a number'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
        # ✅ تنفيذ الحذف مباشرة (بدون تحذير)
        count = SecurityLog.cleanup_old_logs(days=days)
    
        return Response({
            'status': 'success',
            'message': f'Deleted {count} logs older than {days} days',
            'deleted_count': count,
            'days': days
        })    


class SessionViewSet(viewsets.ModelViewSet):
    """ViewSet للجلسات"""
    
    queryset = Session.objects.all()
    serializer_class = SessionSerializer
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        user_id = self.request.query_params.get('user_id')
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            is_active = is_active.lower() == 'true'
            queryset = queryset.filter(is_active=is_active)
        
        return queryset
    
    @action(detail=True, methods=['post'])
    def terminate(self, request, pk=None):
        """إنهاء جلسة محددة"""
        session = self.get_object()
        session.is_active = False
        session.save()
        
        # ✅ تسجيل الحدث
        SecurityLog.objects.create(
            user=request.user,
            event_type='session_terminated',
            severity='info',
            ip_address=request.META.get('REMOTE_ADDR'),
            details={'session_user': session.user.username}
        )
        
        # ✅ تحديث الإحصائيات
        self._update_stats()
        
        return Response({
            'status': 'Session terminated',
            'session_id': session.id,
            'user': session.user.username
        })
    
    @action(detail=False, methods=['post'])
    def terminate_all(self, request):
        """إنهاء جميع جلسات المستخدم الحالي"""
        user = request.user
        count = Session.objects.filter(user=user, is_active=True).update(is_active=False)
        
        # ✅ تسجيل الحدث
        SecurityLog.objects.create(
            user=user,
            event_type='session_terminated',
            severity='info',
            ip_address=request.META.get('REMOTE_ADDR'),
            details={'terminated': 'all_sessions', 'count': count}
        )
        
        # ✅ تحديث الإحصائيات
        self._update_stats()
        
        return Response({
            'status': 'All sessions terminated',
            'terminated_count': count,
            'user': user.username
        })
    
    @action(detail=False, methods=['post'])
    def terminate_all_except_current(self, request):
        """
        ✅ إنهاء جميع جلسات المستخدمين الآخرين (ما عدا الجلسة الحالية)
        """
        current_user = request.user
        current_session_key = request.session.session_key
        
        # ✅ إنهاء جميع الجلسات النشطة للمستخدمين الآخرين
        terminated = Session.objects.filter(is_active=True).exclude(
            user=current_user
        )
        count = terminated.count()
        terminated.update(is_active=False)
        
        # ✅ تسجيل الحدث
        SecurityLog.objects.create(
            user=current_user,
            event_type='session_terminated',
            severity='info',
            ip_address=request.META.get('REMOTE_ADDR', '127.0.0.1'),
            details={
                'terminated_sessions': count,
                'action': 'terminate_all_except_current',
                'current_user': current_user.username
            }
        )
        
        # ✅ تحديث الإحصائيات
        self._update_stats()
        
        return Response({
            'status': 'success',
            'message': f'Terminated {count} session(s) for other users',
            'terminated_count': count
        })
    
    @action(detail=False, methods=['post'])
    def create_session(self, request):
        """إنشاء جلسة للمستخدم الحالي"""
        
        user = request.user
        
        # ✅ التأكد من وجود session_key
        session_key = request.session.session_key
        if not session_key:
            request.session.create()
            session_key = request.session.session_key
        
        # ✅ إنهاء الجلسات القديمة
        Session.objects.filter(user=user, is_active=True).update(is_active=False)
        
        # ✅ إنشاء جلسة جديدة
        session = Session.objects.create(
            user=user,
            session_key=session_key,
            ip_address=request.META.get('REMOTE_ADDR', '127.0.0.1'),
            user_agent=request.META.get('HTTP_USER_AGENT', 'Unknown'),
            device_type='Desktop',
            expires_at=timezone.now() + timezone.timedelta(days=7),
            is_active=True
        )
        
        # ✅ تسجيل الحدث
        SecurityLog.objects.create(
            user=user,
            event_type='session_created',
            severity='info',
            ip_address=request.META.get('REMOTE_ADDR', '127.0.0.1'),
            details={'session_id': session.id}
        )
        
        # ✅ تحديث الإحصائيات
        self._update_stats()
        
        return Response({
            'status': 'Session created',
            'user': user.username,
            'session_id': session.id
        })
    
    @action(detail=False, methods=['post'])
    def cleanup(self, request):
        """
        ✅ تنظيف الجلسات المنتهية وغير النشطة يدوياً
        """
        # ✅ حذف الجلسات المنتهية
        expired_count = Session.cleanup_expired()
        
        # ✅ حذف الجلسات غير النشطة
        days = getattr(settings, 'INACTIVE_SESSION_RETENTION_DAYS', 7)
        inactive_count = Session.cleanup_inactive(days=days)
        
        # ✅ تسجيل الحدث
        SecurityLog.objects.create(
            user=request.user,
            event_type='session_terminated',
            severity='info',
            ip_address=request.META.get('REMOTE_ADDR', '127.0.0.1'),
            details={
                'action': 'manual_cleanup',
                'expired_removed': expired_count,
                'inactive_removed': inactive_count
            }
        )
        
        # ✅ تحديث الإحصائيات
        self._update_stats()
        
        return Response({
            'status': 'success',
            'message': 'Sessions cleaned up successfully',
            'expired_removed': expired_count,
            'inactive_removed': inactive_count,
            'total_removed': expired_count + inactive_count
        })
    
    @action(detail=False, methods=['post'])
    def clear_user_sessions(self, request):
        """
        ✅ حذف جميع جلسات المستخدم (بما فيها غير النشطة)
        """
        user = request.user
        
        # ✅ حذف جميع الجلسات لهذا المستخدم
        total = Session.objects.filter(user=user).count()
        Session.objects.filter(user=user).delete()
        
        # ✅ تسجيل الحدث
        SecurityLog.objects.create(
            user=user,
            event_type='session_terminated',
            severity='info',
            ip_address=request.META.get('REMOTE_ADDR', '127.0.0.1'),
            details={
                'action': 'clear_all_sessions',
                'deleted_count': total
            }
        )
        
        # ✅ تحديث الإحصائيات
        self._update_stats()
        
        return Response({
            'status': 'success',
            'message': f'All sessions for {user.username} have been cleared',
            'deleted_count': total
        })
    
    @action(detail=False, methods=['get'])
    def session_stats(self, request):
        """
        ✅ إحصائيات الجلسات
        """
        total = Session.objects.count()
        active = Session.objects.filter(is_active=True).count()
        inactive = Session.objects.filter(is_active=False).count()
        expired = Session.objects.filter(expires_at__lt=timezone.now()).count()
        
        # ✅ عدد الجلسات لكل مستخدم
        per_user = {}
        for session in Session.objects.all():
            username = session.user.username
            per_user[username] = per_user.get(username, 0) + 1
        
        return Response({
            'total': total,
            'active': active,
            'inactive': inactive,
            'expired': expired,
            'per_user': per_user,
            'recommendation': 'Run cleanup to remove expired sessions' if expired > 0 else 'All sessions are healthy'
        })
    
    def _update_stats(self):
        """تحديث إحصائيات الأمان"""
        try:
            stats, created = SecurityStats.objects.get_or_create(id=1)
            
            stats.total_users = User.objects.count()
            stats.active_users = User.objects.filter(is_active=True).count()
            stats.locked_users = User.objects.filter(is_active=False).count()
            stats.admin_users = User.objects.filter(is_superuser=True).count()
            
            stats.two_factor_enabled = UserSecurity.objects.filter(two_factor_enabled=True).count()
            stats.strong_passwords = UserSecurity.objects.filter(has_strong_password=True).count()
            stats.secure_sessions = UserSecurity.objects.filter(secure_session=True).count()
            
            stats.active_sessions = Session.objects.filter(is_active=True).count()
            
            stats.save()
            print(f"📊 Stats updated: active={stats.active_users}, locked={stats.locked_users}")
        except Exception as e:
            print(f"⚠️ Could not update stats: {e}")


class SecurityStatsViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet لإحصائيات الأمان"""
    
    queryset = SecurityStats.objects.all()
    serializer_class = SecurityStatsSerializer
    permission_classes = [AllowAny]
    
    @action(detail=False, methods=['get'])
    def latest(self, request):
        """الحصول على أحدث الإحصائيات"""
        stats = SecurityStats.objects.first()
        if not stats:
            stats = self._generate_stats()
        
        serializer = self.get_serializer(stats)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def refresh(self, request):
        """تحديث الإحصائيات"""
        stats = self._generate_stats()
        serializer = self.get_serializer(stats)
        return Response(serializer.data)
    
    def _generate_stats(self):
        """توليد إحصائيات جديدة"""
        stats, created = SecurityStats.objects.get_or_create(id=1)
        
        stats.total_users = User.objects.count()
        stats.active_users = User.objects.filter(is_active=True).count()
        stats.locked_users = User.objects.filter(is_active=False).count()
        stats.admin_users = User.objects.filter(is_superuser=True).count()
        
        stats.two_factor_enabled = UserSecurity.objects.filter(two_factor_enabled=True).count()
        stats.strong_passwords = UserSecurity.objects.filter(has_strong_password=True).count()
        stats.secure_sessions = UserSecurity.objects.filter(secure_session=True).count()
        
        stats.active_sessions = Session.objects.filter(is_active=True).count()
        
        today = timezone.now().date()
        stats.failed_logins_today = SecurityLog.objects.filter(
            event_type='failed_login',
            created_at__date=today
        ).count()
        
        week_ago = today - timedelta(days=7)
        stats.failed_logins_week = SecurityLog.objects.filter(
            event_type='failed_login',
            created_at__date__gte=week_ago
        ).count()
        
        stats.save()
        return stats


class UserSecurityViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet لإعدادات أمان المستخدمين"""
    
    queryset = UserSecurity.objects.all()
    serializer_class = UserSecuritySerializer
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        user_id = self.request.query_params.get('user_id')
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        
        return queryset