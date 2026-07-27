# analytics/views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import timedelta
from orders.models import Order
from customers.models import Customer
from products.models import Product


def calculate_growth(current, previous):
    """
    حساب النمو مع التحقق من الأخطاء
    - يحول القيم إلى float
    - يتعامل مع القسمة على صفر
    - يحد من النمو في نطاق معقول
    """
    # ✅ تحويل إلى float
    current = float(current) if current is not None else 0.0
    previous = float(previous) if previous is not None else 0.0
    
    # ✅ إذا كانت القيمة السابقة 0، لا يمكن حساب النمو
    if previous == 0:
        return 0.0
    
    # ✅ إذا كانت القيمة الحالية 0، النمو = -100%
    if current == 0:
        return -100.0
    
    # ✅ حساب النمو
    growth = ((current - previous) / previous) * 100
    
    # ✅ تحديد النمو في نطاق معقول
    if growth < -100:
        growth = -100.0
    elif growth > 1000:
        growth = 1000.0
    
    return growth


@api_view(['GET'])
@permission_classes([AllowAny])
def dashboard_metrics(request):
    """
    Dashboard Metrics - Professional Implementation
    جميع البيانات محسوبة من قاعدة البيانات
    """
    try:
        now = timezone.now()
        
        # 📅 تحديد الفترات الزمنية
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        last_month_start = (month_start - timedelta(days=1)).replace(day=1)
        three_months_ago = (month_start - timedelta(days=90))
        
        print(f"📅 Month Start: {month_start}")
        print(f"📅 Last Month Start: {last_month_start}")
        
        # ============================================
        # 1️⃣ جميع الطلبات (لتحليل الأداء)
        # ============================================
        all_orders = Order.objects.exclude(status='cancelled')
        all_orders_current = all_orders.filter(created_at__gte=month_start)
        all_orders_previous = all_orders.filter(
            created_at__gte=last_month_start,
            created_at__lt=month_start
        )
        
        # ============================================
        # 2️⃣ الطلبات المسلمة (للتقارير المالية)
        # ============================================
        delivered_orders = Order.objects.filter(status='delivered')
        delivered_current = delivered_orders.filter(created_at__gte=month_start)
        delivered_previous = delivered_orders.filter(
            created_at__gte=last_month_start,
            created_at__lt=month_start
        )
        
        # ============================================
        # 3️⃣ حساب الإيرادات والطلبات
        # ============================================
        
        # من جميع الطلبات (لأداء المتجر)
        total_revenue = all_orders.aggregate(total=Sum('total_amount'))['total'] or 0
        total_orders = all_orders.count()
        
        current_revenue = all_orders_current.aggregate(total=Sum('total_amount'))['total'] or 0
        current_orders = all_orders_current.count()
        
        previous_revenue = all_orders_previous.aggregate(total=Sum('total_amount'))['total'] or 0
        previous_orders = all_orders_previous.count()
        
        # من الطلبات المسلمة (للتقارير المالية)
        delivered_revenue = delivered_orders.aggregate(total=Sum('total_amount'))['total'] or 0
        delivered_orders_count = delivered_orders.count()
        
        delivered_current_revenue = delivered_current.aggregate(total=Sum('total_amount'))['total'] or 0
        delivered_current_orders = delivered_current.count()
        
        delivered_previous_revenue = delivered_previous.aggregate(total=Sum('total_amount'))['total'] or 0
        delivered_previous_orders = delivered_previous.count()
        
        # ============================================
        # 4️⃣ حساب النمو (بطريقة احترافية)
        # ============================================
        
        # ✅ نمو جميع الطلبات
        revenue_growth = calculate_growth(current_revenue, previous_revenue)
        orders_growth = calculate_growth(current_orders, previous_orders)
        
        # ✅ نمو الطلبات المسلمة
        delivered_revenue_growth = calculate_growth(delivered_current_revenue, delivered_previous_revenue)
        delivered_orders_growth = calculate_growth(delivered_current_orders, delivered_previous_orders)
        
        # ✅ نمو العملاء الجدد
        total_customers = Customer.objects.count()
        new_customers_current = Customer.objects.filter(created_at__gte=month_start).count()
        new_customers_previous = Customer.objects.filter(
            created_at__gte=last_month_start,
            created_at__lt=month_start
        ).count()
        customers_growth = calculate_growth(new_customers_current, new_customers_previous)
        
        print(f"📊 All Orders - Current: ${current_revenue:,.2f} ({current_orders} orders)")
        print(f"📊 All Orders - Previous: ${previous_revenue:,.2f} ({previous_orders} orders)")
        print(f"📈 All Orders Growth: {revenue_growth:+.1f}%")
        print(f"📊 Delivered - Current: ${delivered_current_revenue:,.2f} ({delivered_current_orders} orders)")
        print(f"📊 Delivered - Previous: ${delivered_previous_revenue:,.2f} ({delivered_previous_orders} orders)")
        print(f"📈 Delivered Growth: {delivered_revenue_growth:+.1f}%")
        
        # ============================================
        # 5️⃣ العملاء
        # ============================================
        active_customers = Customer.objects.filter(orders__isnull=False).distinct().count()
        new_customers = Customer.objects.filter(created_at__gte=month_start).count()
        
        # ============================================
        # 6️⃣ حساب Performance Score (من جميع الطلبات)
        # ============================================
        max_revenue = float(max(100000, total_revenue))
        max_orders = float(max(20, total_orders))
        max_customers = float(max(10, active_customers))
        
        total_revenue_float = float(total_revenue)
        total_orders_float = float(total_orders)
        active_customers_float = float(active_customers)
        
        revenue_score = float(min((total_revenue_float / max_revenue) * 50, 50))
        orders_score = float(min((total_orders_float / max_orders) * 30, 30))
        customers_score = float(min((active_customers_float / max_customers) * 20, 20))
        
        performance_score = round(revenue_score + orders_score + customers_score)
        
        # ============================================
        # 7️⃣ Resource Efficiency
        # ============================================
        avg_orders_per_active = total_orders_float / active_customers_float if active_customers_float > 0 else 0
        efficiency_score = float(min((avg_orders_per_active / 5) * 10, 10))
        
        # ============================================
        # 8️⃣ بيانات المنتجات
        # ============================================
        products = Product.objects.all()
        total_products = products.count()
        
        inventory_value = 0
        for p in products:
            if p.price and p.quantity:
                inventory_value += float(p.price) * int(p.quantity)
        
        # ============================================
        # 9️⃣ المقاييس الإضافية
        # ============================================
        avg_order_value = total_revenue_float / total_orders_float if total_orders_float > 0 else 0
        conversion_rate = (active_customers_float / float(total_customers) * 100) if total_customers > 0 else 0
        
        # ============================================
        # 📊 توزيع حالات الطلبات
        # ============================================
        orders_by_status = {}
        for status in ['pending', 'processing', 'shipped', 'delivered', 'cancelled']:
            count = Order.objects.filter(status=status).count()
            orders_by_status[status] = count
        
        # ============================================
        # ✅ الرد النهائي الاحترافي
        # ============================================
        return Response({
            # 📊 أداء المتجر (من جميع الطلبات)
            'performance': {
                'score': performance_score,
                'revenue': float(total_revenue),
                'orders': total_orders,
                'active_customers': active_customers,
                'growth': {
                    'revenue': float(revenue_growth),
                    'orders': float(orders_growth),
                    'customers': float(customers_growth)
                }
            },
            
            # 💰 الإيرادات الفعلية (من الطلبات المسلمة فقط)
            'financial': {
                'revenue': float(delivered_revenue),
                'orders': delivered_orders_count,
                'growth': {
                    'revenue': float(delivered_revenue_growth),
                    'orders': float(delivered_orders_growth)
                }
            },
            
            # ⚡ Resource Efficiency
            'efficiency': {
                'score': float(efficiency_score),
                'avg_orders_per_customer': float(avg_orders_per_active)
            },
            
            # 📈 المقاييس التفصيلية
            'details': {
                'current_month': {
                    'all_orders': current_orders,
                    'all_revenue': float(current_revenue),
                    'delivered_orders': delivered_current_orders,
                    'delivered_revenue': float(delivered_current_revenue)
                },
                'previous_month': {
                    'all_orders': previous_orders,
                    'all_revenue': float(previous_revenue),
                    'delivered_orders': delivered_previous_orders,
                    'delivered_revenue': float(delivered_previous_revenue)
                },
                'orders_by_status': orders_by_status
            },
            
            # 📊 المقاييس الإضافية
            'metrics': {
                'total_customers': total_customers,
                'new_customers': new_customers,
                'conversion_rate': float(conversion_rate),
                'avg_order_value': float(avg_order_value),
                'inventory_value': float(inventory_value),
                'total_products': total_products
            }
        })
        
    except Exception as e:
        print(f"❌ Error in dashboard_metrics: {str(e)}")
        import traceback
        traceback.print_exc()
        return Response({'error': str(e)}, status=500)


@api_view(['GET'])
@permission_classes([AllowAny])
def sales_data(request):
    """بيانات المبيعات للرسم البياني مع حساب النمو"""
    try:
        period = request.query_params.get('period', 'month')
        status_filter = request.query_params.get('status', 'all')
        
        now = timezone.now()
        
        if period == 'week':
            start_date = now - timedelta(days=7)
        elif period == 'month':
            start_date = now - timedelta(days=30)
        else:
            start_date = now - timedelta(days=365)
        
        if status_filter == 'delivered':
            orders = Order.objects.filter(
                created_at__gte=start_date,
                status='delivered'
            )
        else:
            orders = Order.objects.filter(created_at__gte=start_date).exclude(status='cancelled')
        
        # ✅ توليد البيانات حسب الفترة
        if period == 'week':
            result = []
            for i in range(7):
                day = now - timedelta(days=6-i)
                day_orders = orders.filter(created_at__date=day.date())
                result.append({
                    'date': day.strftime('%a'),
                    'sales': float(day_orders.aggregate(total=Sum('total_amount'))['total'] or 0),
                    'orders': day_orders.count()
                })
        elif period == 'month':
            result = []
            for i in range(4):
                week_start = now - timedelta(days=(3-i)*7 + now.weekday())
                week_end = week_start + timedelta(days=6)
                week_orders = orders.filter(
                    created_at__date__gte=week_start.date(),
                    created_at__date__lte=week_end.date()
                )
                result.append({
                    'date': f'Week {i+1}',
                    'sales': float(week_orders.aggregate(total=Sum('total_amount'))['total'] or 0),
                    'orders': week_orders.count()
                })
        else:
            result = []
            for i in range(12):
                month_date = now.replace(day=1) - timedelta(days=30*(11-i))
                month_orders = orders.filter(
                    created_at__year=month_date.year,
                    created_at__month=month_date.month
                )
                result.append({
                    'date': month_date.strftime('%b'),
                    'sales': float(month_orders.aggregate(total=Sum('total_amount'))['total'] or 0),
                    'orders': month_orders.count()
                })
        
        # ✅ حساب النمو من البيانات
        growth = 0
        if len(result) >= 2:
            mid = len(result) // 2
            first_half = result[:mid]
            second_half = result[mid:]
            
            first_avg = sum(item['sales'] for item in first_half) / len(first_half) if first_half else 0
            second_avg = sum(item['sales'] for item in second_half) / len(second_half) if second_half else 0
            
            if first_avg > 0 and second_avg > 0:
                growth = ((second_avg - first_avg) / first_avg) * 100
        
        print(f"📊 Sales Data: {len(result)} points, Growth: {growth:.1f}%")
        
        return Response({
            'data': result,
            'growth': round(growth, 1)
        })
            
    except Exception as e:
        print(f"❌ Error in sales_data: {str(e)}")
        return Response({'error': str(e)}, status=500)


@api_view(['GET'])
@permission_classes([AllowAny])
def revenue_data(request):
    """بيانات الإيرادات"""
    try:
        period = request.query_params.get('period', 'month')
        
        now = timezone.now()
        
        if period == 'week':
            start_date = now - timedelta(days=7)
        elif period == 'month':
            start_date = now - timedelta(days=30)
        else:
            start_date = now - timedelta(days=365)
        
        orders = Order.objects.filter(
            created_at__gte=start_date,
            status='delivered'
        )
        
        total_revenue = orders.aggregate(total=Sum('total_amount'))['total'] or 0
        
        return Response({
            'total_revenue': float(total_revenue),
            'period': period,
            'orders_count': orders.count()
        })
        
    except Exception as e:
        print(f"❌ Error in revenue_data: {str(e)}")
        return Response({'error': str(e)}, status=500)