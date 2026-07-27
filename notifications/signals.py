# notifications/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.db.models import Sum
from django.utils import timezone
from datetime import timedelta
from orders.models import Order, OrderItem
from products.models import Product
from customers.models import Customer
from .models import Notification


@receiver(post_save, sender=Product)
def create_stock_notification(sender, instance, **kwargs):
    """إنشاء تنبيه عند تغيير مخزون المنتج"""
    print(f"🔍 Signal triggered for: {instance.name} (Quantity: {instance.quantity})")

    if instance.quantity <= 10:
        all_users = User.objects.all()
        
        if instance.quantity == 0:
            status = 'Out of Stock'
            icon = 'AlertCircle'
            color = '#F08FAE'
            link = '/low-stock'
        else:
            status = 'Low Stock'
            icon = 'AlertTriangle'
            color = '#EE9C6C'
            link = '/low-stock'
        
        for user in all_users:
            existing = Notification.objects.filter(
                user=user,
                message__icontains=instance.name,
                is_read=False
            ).exists()
            
            if not existing:
                Notification.objects.create(
                    user=user,
                    title=f"{status}: {instance.name}",
                    message=f"Quantity: {instance.quantity} units remaining",
                    type='stock',
                    icon=icon,
                    color=color,
                    link=link
                )
                print(f"✅ Stock notification sent to {user.username}")


@receiver(post_save, sender=Order)
def create_order_notification(sender, instance, created, **kwargs):
    """إنشاء تنبيه عند إنشاء طلب جديد"""
    if created:
        all_users = User.objects.all()
        for user in all_users:
            Notification.objects.create(
                user=user,
                title=f"New Order #{instance.order_number}",
                message=f"Order placed by {instance.customer.name} - Total: ${instance.total_amount}",
                type='order',
                icon='ShoppingBag',
                color='#8B7ABA',
                link=f'/orders/{instance.id}'
            )
            print(f"✅ Order notification sent to {user.username}")


@receiver(post_save, sender=OrderItem)
def check_order_status(sender, instance, **kwargs):
    """التحقق من الطلبات المعلقة بعد إضافة عنصر جديد"""
    order = instance.order
    if order.status == 'pending':
        all_users = User.objects.all()
        for user in all_users:
            existing = Notification.objects.filter(
                user=user,
                link=f'/orders/{order.id}',
                is_read=False
            ).exists()
            
            if not existing:
                Notification.objects.create(
                    user=user,
                    title=f"Pending Order #{order.order_number}",
                    message=f"Order #{order.order_number} is waiting for processing",
                    type='order',
                    icon='Clock',
                    color='#EE9C6C',
                    link=f'/orders/{order.id}'
                )
                print(f"✅ Pending order notification sent to {user.username}")


# ========== تنبيهات العملاء ==========

@receiver(post_save, sender=Customer)
def create_customer_notification(sender, instance, created, **kwargs):
    """إنشاء تنبيه عند إنشاء عميل جديد - يرسل فقط للمشرفين"""
    if created:
        admin_users = User.objects.filter(is_superuser=True)
        
        for user in admin_users:
            Notification.objects.create(
                user=user,
                title=f"New Customer: {instance.name}",
                message=f"{instance.name} has registered with email: {instance.email}",
                type='system',
                icon='UserPlus',
                color='#34D19C',
                link=f'/customers/{instance.id}'
            )
            print(f"✅ Customer notification sent to admin {user.username}")
        
        if not admin_users.exists():
            first_user = User.objects.first()
            if first_user:
                Notification.objects.create(
                    user=first_user,
                    title=f"New Customer: {instance.name}",
                    message=f"{instance.name} has registered with email: {instance.email}",
                    type='system',
                    icon='UserPlus',
                    color='#34D19C',
                    link=f'/customers/{instance.id}'
                )
                print(f"✅ Customer notification sent to {first_user.username}")


@receiver(post_save, sender=Customer)
def update_customer_notification(sender, instance, **kwargs):
    """إنشاء تنبيه عند زيادة عدد طلبات العميل (كل 5 طلبات)"""
    if instance.total_orders > 0 and instance.total_orders % 5 == 0:
        admin_users = User.objects.filter(is_superuser=True)
        
        for user in admin_users:
            existing = Notification.objects.filter(
                user=user,
                message__icontains=f"{instance.name} has placed",
                is_read=False
            ).exists()
            
            if not existing:
                Notification.objects.create(
                    user=user,
                    title=f"Milestone: {instance.name}",
                    message=f"{instance.name} has placed {instance.total_orders} orders! Total spent: ${instance.total_spent}",
                    type='system',
                    icon='User',
                    color='#EE9C6C',
                    link=f'/customers/{instance.id}'
                )
                print(f"✅ Milestone notification sent to admin {user.username}")


# ========== تنبيهات تحقيق الأهداف ==========

@receiver(post_save, sender=Order)
def check_sales_target(sender, instance, **kwargs):
    """التحقق من تحقيق أهداف المبيعات"""
    
    # ✅ أهداف المبيعات
    TARGETS = {
        'orders': 10,
        'revenue': 10000,
        'monthly_growth': 20,
    }
    
    # ✅ حساب إجمالي الطلبات
    total_orders = Order.objects.count()
    
    # ✅ حساب إجمالي الإيرادات
    total_revenue = Order.objects.filter(
        status='delivered'
    ).aggregate(total=Sum('total_amount'))['total'] or 0
    
    # ✅ حساب نمو هذا الشهر
    now = timezone.now()
    this_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    last_month_start = (this_month_start - timedelta(days=1)).replace(day=1)
    
    this_month_orders = Order.objects.filter(
        created_at__gte=this_month_start,
        status='delivered'
    ).count()
    
    last_month_orders = Order.objects.filter(
        created_at__gte=last_month_start,
        created_at__lt=this_month_start,
        status='delivered'
    ).count()
    
    monthly_growth = 0
    if last_month_orders > 0:
        monthly_growth = ((this_month_orders - last_month_orders) / last_month_orders) * 100
    
    admin_users = User.objects.filter(is_superuser=True)
    
    # 1. هدف الطلبات
    if total_orders >= TARGETS['orders']:
        existing = Notification.objects.filter(
            title__icontains='Orders Target Achieved',
            is_read=False
        ).exists()
        
        if not existing:
            for user in admin_users:
                Notification.objects.create(
                    user=user,
                    title=f"Orders Target Achieved!",
                    message=f"🎉 Congratulations! You've reached {total_orders} orders! Target was {TARGETS['orders']}.",
                    type='system',
                    icon='Award',
                    color='#34D19C',
                    link='/orders'
                )
                print(f"✅ Orders target notification sent to {user.username}")
    
    # 2. هدف الإيرادات
    if total_revenue >= TARGETS['revenue']:
        existing = Notification.objects.filter(
            title__icontains='Revenue Target Achieved',
            is_read=False
        ).exists()
        
        if not existing:
            for user in admin_users:
                Notification.objects.create(
                    user=user,
                    title=f"Revenue Target Achieved!",
                    message=f"🎉 Congratulations! You've reached ${total_revenue:,.2f} in revenue! Target was ${TARGETS['revenue']:,.2f}.",
                    type='system',
                    icon='DollarSign',
                    color='#EE9C6C',
                    link='/revenue'
                )
                print(f"✅ Revenue target notification sent to {user.username}")
    
    # 3. هدف النمو الشهري
    if monthly_growth >= TARGETS['monthly_growth']:
        existing = Notification.objects.filter(
            title__icontains='Growth Target Achieved',
            is_read=False
        ).exists()
        
        if not existing:
            for user in admin_users:
                Notification.objects.create(
                    user=user,
                    title=f"Growth Target Achieved!",
                    message=f"🎉 Congratulations! Monthly growth is {monthly_growth:.1f}%! Target was {TARGETS['monthly_growth']}%.",
                    type='system',
                    icon='TrendingUp',
                    color='#8B7ABA',
                    link='/analytics'
                )
                print(f"✅ Growth target notification sent to {user.username}")