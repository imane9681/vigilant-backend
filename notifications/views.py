# notifications/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Notification
from .serializers import NotificationSerializer

class NotificationViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """الحصول على عدد التنبيهات غير المقروءة"""
        count = Notification.objects.filter(user=request.user, is_read=False).count()
        return Response({'unread_count': count})
    
    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """تحديد تنبيه كمقروء"""
        notification = self.get_object()
        notification.is_read = True
        notification.save()
        return Response({'status': 'marked as read'})
    
    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        """تحديد جميع التنبيهات كمقروءة"""
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return Response({'status': 'all marked as read'})
    
    @action(detail=True, methods=['delete'])
    def delete_notification(self, request, pk=None):
        """حذف تنبيه"""
        notification = self.get_object()
        notification.delete()
        return Response({'status': 'deleted'}, status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=False, methods=['delete'])
    def clear_all(self, request):
        """حذف جميع التنبيهات"""
        Notification.objects.filter(user=request.user).delete()
        return Response({'status': 'all cleared'}, status=status.HTTP_204_NO_CONTENT)