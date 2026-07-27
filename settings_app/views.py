# settings_app/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth.models import User
from .models import GeneralSettings, NotificationSettings, SecuritySettings
from .serializers import (
    GeneralSettingsSerializer,
    NotificationSettingsSerializer,
    SecuritySettingsSerializer
)


class GeneralSettingsViewSet(viewsets.ModelViewSet):
    """
    ViewSet للإعدادات العامة
    """
    
    queryset = GeneralSettings.objects.all()
    serializer_class = GeneralSettingsSerializer
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        # ✅ التأكد من وجود إعدادات
        if not GeneralSettings.objects.exists():
            GeneralSettings.objects.create()
        return GeneralSettings.objects.all()
    
    def retrieve(self, request, pk=None):
        """الحصول على إعدادات عامة محددة"""
        try:
            instance = GeneralSettings.objects.get(pk=pk)
            serializer = self.get_serializer(instance)
            return Response(serializer.data)
        except GeneralSettings.DoesNotExist:
            # ✅ إنشاء إعدادات جديدة إذا لم تكن موجودة
            instance = GeneralSettings.objects.create()
            serializer = self.get_serializer(instance)
            return Response(serializer.data)
    
    def update(self, request, pk=None, partial=True):
        """
        ✅ تحديث إعدادات عامة محددة مع إعادة البيانات المحدثة
        """
        try:
            instance = GeneralSettings.objects.get(pk=pk)
            
            # ✅ استخدام serializer لتحديث البيانات
            serializer = self.get_serializer(instance, data=request.data, partial=partial)
            
            if serializer.is_valid():
                serializer.save()
                
                # ✅ ✅ ✅ إعادة البيانات المحدثة بالكامل
                updated_instance = GeneralSettings.objects.get(pk=pk)
                updated_serializer = self.get_serializer(updated_instance)
                return Response(updated_serializer.data)
            else:
                print(f"❌ Validation errors: {serializer.errors}")
                return Response(
                    {'errors': serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
        except GeneralSettings.DoesNotExist:
            # ✅ إذا لم توجد الإعدادات، قم بإنشائها
            instance = GeneralSettings.objects.create()
            serializer = self.get_serializer(instance, data=request.data, partial=partial)
            if serializer.is_valid():
                serializer.save()
                
                # ✅ ✅ ✅ إعادة البيانات المحدثة
                updated_instance = GeneralSettings.objects.get(pk=instance.pk)
                updated_serializer = self.get_serializer(updated_instance)
                return Response(updated_serializer.data)
            
            return Response(
                {'error': 'Settings not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            print(f"❌ Error updating settings: {str(e)}")
            import traceback
            traceback.print_exc()
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def list(self, request):
        """الحصول على جميع الإعدادات العامة"""
        # ✅ التأكد من وجود إعدادات
        if not GeneralSettings.objects.exists():
            GeneralSettings.objects.create()
        
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class NotificationSettingsViewSet(viewsets.ModelViewSet):
    """
    ViewSet لإعدادات الإشعارات
    """
    
    queryset = NotificationSettings.objects.all()
    serializer_class = NotificationSettingsSerializer
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        return NotificationSettings.objects.filter(user=self.request.user)
    
    def update(self, request, pk=None, partial=True):
        """
        ✅ تحديث إعدادات الإشعارات مع إعادة البيانات المحدثة
        """
        try:
            instance = NotificationSettings.objects.get(pk=pk)
            serializer = self.get_serializer(instance, data=request.data, partial=partial)
            
            if serializer.is_valid():
                serializer.save()
                
                # ✅ ✅ ✅ إعادة البيانات المحدثة
                updated_instance = NotificationSettings.objects.get(pk=pk)
                updated_serializer = self.get_serializer(updated_instance)
                return Response(updated_serializer.data)
            else:
                return Response(
                    {'errors': serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except NotificationSettings.DoesNotExist:
            # ✅ إنشاء إعدادات جديدة للمستخدم
            user = request.user
            if user.is_authenticated:
                instance = NotificationSettings.objects.create(user=user)
                serializer = self.get_serializer(instance, data=request.data, partial=partial)
                if serializer.is_valid():
                    serializer.save()
                    
                    # ✅ ✅ ✅ إعادة البيانات المحدثة
                    updated_instance = NotificationSettings.objects.get(pk=instance.pk)
                    updated_serializer = self.get_serializer(updated_instance)
                    return Response(updated_serializer.data)
            return Response(
                {'error': 'Settings not found'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['get'])
    def my_settings(self, request):
        """الحصول على إعدادات الإشعارات للمستخدم الحالي"""
        if not request.user.is_authenticated:
            return Response(
                {'error': 'User not authenticated'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        settings, created = NotificationSettings.objects.get_or_create(user=request.user)
        serializer = self.get_serializer(settings)
        return Response(serializer.data)


class SecuritySettingsViewSet(viewsets.ModelViewSet):
    """
    ViewSet لإعدادات الأمان
    """
    
    queryset = SecuritySettings.objects.all()
    serializer_class = SecuritySettingsSerializer
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        return SecuritySettings.objects.filter(user=self.request.user)
    
    def update(self, request, pk=None, partial=True):
        """
        ✅ تحديث إعدادات الأمان مع إعادة البيانات المحدثة
        """
        try:
            instance = SecuritySettings.objects.get(pk=pk)
            serializer = self.get_serializer(instance, data=request.data, partial=partial)
            
            if serializer.is_valid():
                serializer.save()
                
                # ✅ ✅ ✅ إعادة البيانات المحدثة
                updated_instance = SecuritySettings.objects.get(pk=pk)
                updated_serializer = self.get_serializer(updated_instance)
                return Response(updated_serializer.data)
            else:
                return Response(
                    {'errors': serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except SecuritySettings.DoesNotExist:
            # ✅ إنشاء إعدادات جديدة للمستخدم
            user = request.user
            if user.is_authenticated:
                instance = SecuritySettings.objects.create(user=user)
                serializer = self.get_serializer(instance, data=request.data, partial=partial)
                if serializer.is_valid():
                    serializer.save()
                    
                    # ✅ ✅ ✅ إعادة البيانات المحدثة
                    updated_instance = SecuritySettings.objects.get(pk=instance.pk)
                    updated_serializer = self.get_serializer(updated_instance)
                    return Response(updated_serializer.data)
            return Response(
                {'error': 'Settings not found'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['get'])
    def my_settings(self, request):
        """الحصول على إعدادات الأمان للمستخدم الحالي"""
        if not request.user.is_authenticated:
            return Response(
                {'error': 'User not authenticated'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        settings, created = SecuritySettings.objects.get_or_create(user=request.user)
        serializer = self.get_serializer(settings)
        return Response(serializer.data)