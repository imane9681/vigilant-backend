# orders/signals.py
from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.db import models
from django.db.models import Sum, F
from .models import Order, OrderItem, Customer
from products.models import Product


@receiver(post_save, sender=Order)
def update_customer_stats_on_order_save(sender, instance, created, **kwargs):
    """تحديث total_orders و total_spent تلقائياً عند حفظ الطلب"""
    customer = instance.customer
    
    customer.total_orders = Order.objects.filter(customer=customer).count()
    customer.total_spent = Order.objects.filter(
        customer=customer, 
        status='delivered'
    ).aggregate(total=Sum('total_amount'))['total'] or 0
    
    customer.save()
    print(f"📊 Updated customer {customer.name}: orders={customer.total_orders}, spent=${customer.total_spent}")


@receiver(post_delete, sender=Order)
def update_customer_stats_on_order_delete(sender, instance, **kwargs):
    """تحديث إحصائيات العميل عند حذف طلب"""
    customer = instance.customer
    
    customer.total_orders = Order.objects.filter(customer=customer).count()
    customer.total_spent = Order.objects.filter(
        customer=customer, 
        status='delivered'
    ).aggregate(total=Sum('total_amount'))['total'] or 0
    
    customer.save()
    print(f"📊 Updated customer {customer.name} after deletion: orders={customer.total_orders}, spent=${customer.total_spent}")


@receiver([post_save, post_delete], sender=OrderItem)
def update_order_total_on_item_change(sender, instance, **kwargs):
    """تحديث total_amount للطلب عند إضافة أو حذف أو تعديل عنصر"""
    order = instance.order
    total = order.items.aggregate(
        total=Sum(F('quantity') * F('price'))
    )['total'] or 0
    order.total_amount = total
    order.save()
    print(f"💰 Updated order {order.order_number} total_amount: ${total}")


# ============================================
# ✅ تحديث كمية المنتج عند إنشاء OrderItem
# ============================================

@receiver(post_save, sender=OrderItem)
def update_product_quantity_on_order_item_create(sender, instance, created, **kwargs):
    """تقليل كمية المنتج عند إنشاء عنصر طلب جديد"""
    if created:
        product = instance.product
        quantity = instance.quantity
        
        if product.quantity >= quantity:
            product.quantity -= quantity
            product.sold_count = (product.sold_count or 0) + quantity
            
            if product.quantity == 0:
                product.in_stock = False
            else:
                product.in_stock = True
            
            product.save()
            print(f"📦 Product {product.name}: quantity reduced by {quantity} (now: {product.quantity})")


# ============================================
# ✅ إعادة كمية المنتج عند حذف OrderItem
# ============================================

@receiver(post_delete, sender=OrderItem)
def restore_product_quantity_on_order_item_delete(sender, instance, **kwargs):
    """إعادة كمية المنتج عند حذف عنصر طلب"""
    product = instance.product
    quantity = instance.quantity
    
    product.quantity += quantity
    product.sold_count = max(0, (product.sold_count or 0) - quantity)
    
    if product.quantity > 0:
        product.in_stock = True
    
    product.save()
    print(f"📦 Product {product.name}: quantity restored by {quantity} (now: {product.quantity})")


# ============================================
# ✅ ✅ ✅ معالجة تغيير حالة الطلب (في الاتجاهين)
# ============================================

@receiver(pre_save, sender=Order)
def handle_order_status_change(sender, instance, **kwargs):
    """
    ✅ ✅ ✅ معالجة تغيير حالة الطلب في الاتجاهين
    - cancelled → other: تنقص الكمية (إلغاء الإلغاء)
    - other → cancelled: تعود الكمية (إلغاء الطلب)
    """
    # ✅ تجنب التكرار
    if hasattr(instance, '_status_change_processed'):
        return
    
    try:
        # ✅ جلب الحالة القديمة
        old_instance = Order.objects.get(pk=instance.pk)
        old_status = old_instance.status
        new_status = instance.status
        
        print(f"📊 Order {instance.order_number}: Status changing from '{old_status}' to '{new_status}'")
        
        # ✅ إذا كانت الحالة تغيرت
        if old_status != new_status:
            
            # ==========================================
            # ✅ الحالة 1: cancelled → other (إلغاء الإلغاء)
            #    يجب أن تنقص الكمية مرة أخرى
            # ==========================================
            if old_status == 'cancelled' and new_status != 'cancelled':
                print(f"🔄 Order {instance.order_number} is being UN-cancelled! Reducing quantities again...")
                
                # ✅ جلب جميع عناصر الطلب
                order_items = OrderItem.objects.filter(order=instance)
                
                for item in order_items:
                    product = item.product
                    quantity = item.quantity
                    
                    # ✅ تقليل الكمية مرة أخرى (لأن الطلب أصبح نشطاً)
                    if product.quantity >= quantity:
                        product.quantity -= quantity
                        product.sold_count = (product.sold_count or 0) + quantity
                        
                        if product.quantity == 0:
                            product.in_stock = False
                        else:
                            product.in_stock = True
                        
                        product.save()
                        print(f"   ✅ Product {product.name}: quantity reduced by {quantity} (now: {product.quantity})")
                    else:
                        print(f"   ⚠️ Not enough stock for {product.name}! Available: {product.quantity}, Need: {quantity}")
                
                print(f"✅ Order {instance.order_number} un-cancelled successfully. Quantities reduced.")
            
            # ==========================================
            # ✅ الحالة 2: other → cancelled (إلغاء الطلب)
            #    يجب أن تعود الكمية
            # ==========================================
            elif new_status == 'cancelled' and old_status != 'cancelled':
                print(f"🔄 Order {instance.order_number} is being cancelled! Restoring product quantities...")
                
                # ✅ جلب جميع عناصر الطلب
                order_items = OrderItem.objects.filter(order=instance)
                
                for item in order_items:
                    product = item.product
                    quantity = item.quantity
                    
                    # ✅ إعادة الكمية للمنتج
                    product.quantity += quantity
                    product.sold_count = max(0, (product.sold_count or 0) - quantity)
                    
                    if product.quantity > 0:
                        product.in_stock = True
                    
                    product.save()
                    print(f"   ✅ Product {product.name}: quantity restored by {quantity} (now: {product.quantity})")
                
                print(f"✅ Order {instance.order_number} cancelled successfully. Quantities restored.")
            
            # ==========================================
            # ✅ الحالة 3: حالات أخرى (pending → processing, etc.)
            #    لا تغيير في الكمية
            # ==========================================
            else:
                print(f"ℹ️ Order {instance.order_number}: Status changed from '{old_status}' to '{new_status}' (no quantity change)")
            
            # ✅ وضع علامة لتجنب التكرار
            instance._status_change_processed = True
            
    except Order.DoesNotExist:
        # ✅ هذا يعني أن الطلب جديد (ليس تحديثاً)
        pass
    except Exception as e:
        print(f"❌ Error in handle_order_status_change: {str(e)}")