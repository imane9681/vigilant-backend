# orders/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import models
from django.db.models import Sum, F
from django.utils import timezone
from .models import Customer, Order, OrderItem
from .serializers import CustomerSerializer, OrderSerializer, OrderWithCustomerSerializer
from products.models import Product


class CustomerViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing customers
    """
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """
        Get customer statistics
        """
        total = Customer.objects.count()
        active = Customer.objects.filter(orders__isnull=False).distinct().count()
        premium = Customer.objects.filter(total_orders__gte=5).count()
        
        total_revenue = Order.objects.exclude(status='cancelled').aggregate(
            total=Sum('total_amount')
        )['total'] or 0
        
        total_orders = Order.objects.exclude(status='cancelled').count()
        average_order_value = total_revenue / total_orders if total_orders > 0 else 0
        
        return Response({
            'total': total,
            'active': active,
            'premium': premium,
            'totalRevenue': float(total_revenue),
            'averageOrderValue': float(average_order_value),
        })


class OrderViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing orders with full CRUD operations
    """
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    
    def create(self, request, *args, **kwargs):
        """
        Create a new order with customer (existing or new)
        """
        print("=" * 60)
        print("Received order data:", request.data)
        print("=" * 60)
        
        serializer = OrderWithCustomerSerializer(data=request.data)
        
        if not serializer.is_valid():
            print("Validation errors:", serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            result = serializer.save()
            return Response(result, status=status.HTTP_201_CREATED)
        except Exception as e:
            print("Error:", str(e))
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """
        Get order statistics - Professional dashboard metrics
        """
        all_orders = Order.objects.exclude(status='cancelled')
        total_orders = all_orders.count()
        total_revenue = all_orders.aggregate(total=Sum('total_amount'))['total'] or 0
        
        delivered_orders = Order.objects.filter(status='delivered')
        delivered_count = delivered_orders.count()
        delivered_revenue = delivered_orders.aggregate(total=Sum('total_amount'))['total'] or 0
        
        pending_orders = Order.objects.filter(status='pending')
        pending_count = pending_orders.count()
        pending_revenue = pending_orders.aggregate(total=Sum('total_amount'))['total'] or 0
        
        processing_orders = Order.objects.filter(status='processing')
        processing_count = processing_orders.count()
        processing_revenue = processing_orders.aggregate(total=Sum('total_amount'))['total'] or 0
        
        shipped_orders = Order.objects.filter(status='shipped')
        shipped_count = shipped_orders.count()
        shipped_revenue = shipped_orders.aggregate(total=Sum('total_amount'))['total'] or 0
        
        cancelled_orders = Order.objects.filter(status='cancelled')
        cancelled_count = cancelled_orders.count()
        cancelled_revenue = cancelled_orders.aggregate(total=Sum('total_amount'))['total'] or 0
        
        completion_rate = round((delivered_count / total_orders * 100) if total_orders > 0 else 0, 1)
        avg_order_value = total_revenue / total_orders if total_orders > 0 else 0
        
        status_distribution = {
            'pending': pending_count,
            'processing': processing_count,
            'shipped': shipped_count,
            'delivered': delivered_count,
            'cancelled': cancelled_count,
        }
        
        return Response({
            'total': total_orders,
            'totalRevenue': float(total_revenue),
            'avgOrderValue': float(avg_order_value),
            'delivered': delivered_count,
            'deliveredRevenue': float(delivered_revenue),
            'pending': pending_count,
            'pendingRevenue': float(pending_revenue),
            'processing': processing_count,
            'processingRevenue': float(processing_revenue),
            'shipped': shipped_count,
            'shippedRevenue': float(shipped_revenue),
            'cancelled': cancelled_count,
            'cancelledRevenue': float(cancelled_revenue),
            'completionRate': completion_rate,
            'statusDistribution': status_distribution,
        })
    
    # ============================================
    # ✅ ✅ ✅ تحديث حالة الطلب
    #    - يتم معالجة الكمية عبر Signal
    #    - الـ View فقط يحدث الحالة
    # ============================================
    
    @action(detail=True, methods=['patch'])
    def update_status(self, request, pk=None):
        """
        ✅ تحديث حالة الطلب
        - يتم معالجة الكمية تلقائياً عبر Signal
        """
        try:
            order = self.get_object()
            new_status = request.data.get('status')
            
            if not new_status:
                return Response(
                    {'error': 'Status is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # ✅ التحقق من صحة الحالة
            valid_statuses = ['pending', 'processing', 'shipped', 'delivered', 'cancelled']
            if new_status not in valid_statuses:
                return Response(
                    {'error': f'Invalid status. Must be one of: {", ".join(valid_statuses)}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # ✅ ✅ ✅ تحديث الحالة فقط
            #    الكمية ستتغير تلقائياً عبر Signal
            order.status = new_status
            order.save()
            
            # ✅ تحديث إحصائيات العميل
            customer = order.customer
            customer.total_orders = Order.objects.filter(customer=customer).count()
            customer.total_spent = Order.objects.filter(
                customer=customer, 
                status='delivered'
            ).aggregate(total=Sum('total_amount'))['total'] or 0
            customer.save()
            
            serializer = self.get_serializer(order)
            return Response({
                'success': True,
                'message': f'Order status updated to {new_status}',
                'order': serializer.data
            })
            
        except Exception as e:
            print(f"❌ Error updating order status: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    # ============================================
    # ✅ ✅ ✅ نقطة نهاية إعادة الطلب
    # ============================================
    
    @action(detail=False, methods=['post'])
    def reorder(self, request):
        """
        ✅ إعادة طلب منتج أو مجموعة منتجات
        """
        try:
            product_id = request.data.get('product_id')
            quantity = request.data.get('quantity', 1)
            supplier = request.data.get('supplier', '')
            priority = request.data.get('priority', 'medium')
            notes = request.data.get('notes', '')
            
            try:
                product = Product.objects.get(id=product_id)
            except Product.DoesNotExist:
                return Response(
                    {'error': f'Product with id {product_id} does not exist'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            if product.quantity < quantity:
                return Response(
                    {'error': f'Not enough stock. Available: {product.quantity}, Requested: {quantity}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            customer = Customer.objects.first()
            if not customer:
                return Response(
                    {'error': 'No customer found. Please create a customer first.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            order = Order.objects.create(
                customer=customer,
                order_number=f"REORDER-{timezone.now().strftime('%Y%m%d%H%M%S')}",
                total_amount=product.price * quantity,
                status='pending',
                payment_method='Reorder',
                shipping_address=customer.address or 'N/A',
                notes=f"Reorder: {product.name} x{quantity}. Priority: {priority}. Supplier: {supplier}. {notes}",
                created_at=timezone.now()
            )
            
            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=quantity,
                price=product.price,
                sold_at=timezone.now()
            )
            
            customer.total_orders = Order.objects.filter(customer=customer).count()
            customer.total_spent = Order.objects.filter(
                customer=customer, 
                status='delivered'
            ).aggregate(total=Sum('total_amount'))['total'] or 0
            customer.save()
            
            return Response({
                'success': True,
                'message': f'Order placed successfully for {product.name}',
                'order': OrderSerializer(order).data,
                'product': {
                    'id': product.id,
                    'name': product.name,
                    'remaining_quantity': product.quantity,
                    'sold_count': product.sold_count
                }
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            print(f"❌ Error in reorder: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )