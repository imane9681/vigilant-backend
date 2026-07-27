# orders/serializers.py
from rest_framework import serializers
from django.db import models
from django.db import transaction
from customers.models import Customer
from .models import Order, OrderItem
from django.utils import timezone


class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ['id', 'name', 'email', 'phone', 'address', 'city', 'country', 'total_orders', 'total_spent', 'created_at']


class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    
    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'product_name', 'quantity', 'price', 'sold_at']


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    customer_name = serializers.CharField(source='customer.name', read_only=True)
    customer_email = serializers.CharField(source='customer.email', read_only=True)
    customer_phone = serializers.CharField(source='customer.phone', read_only=True)
    customer_address = serializers.CharField(source='customer.address', read_only=True)
    
    class Meta:
        model = Order
        fields = ['id', 'order_number', 'customer', 'customer_name', 'customer_email', 
                  'customer_phone', 'customer_address', 'total_amount', 'status', 
                  'payment_method', 'shipping_address', 'notes', 'items', 'created_at', 'updated_at']


class OrderWithCustomerSerializer(serializers.Serializer):
    new_customer = serializers.DictField(required=False, write_only=True)
    existing_customer_id = serializers.IntegerField(required=False, write_only=True)
    
    order_number = serializers.CharField()
    total_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    status = serializers.CharField(default='pending')
    payment_method = serializers.CharField(allow_blank=True, allow_null=True, required=False)
    shipping_address = serializers.CharField()
    notes = serializers.CharField(allow_blank=True, allow_null=True, required=False)
    items = serializers.ListField(child=serializers.DictField())
    
    def validate(self, data):
        if not data.get('existing_customer_id') and not data.get('new_customer'):
            raise serializers.ValidationError("Either existing_customer_id or new_customer is required")
        return data
    
    def create(self, validated_data):
        from django.db import transaction
        from customers.models import Customer
        from products.models import Product
        
        with transaction.atomic():
            # ✅ إنشاء أو جلب العميل
            if validated_data.get('existing_customer_id'):
                customer = Customer.objects.get(id=validated_data['existing_customer_id'])
            else:
                new_customer_data = validated_data.pop('new_customer')
                customer = Customer.objects.create(
                    name=new_customer_data.get('name'),
                    email=new_customer_data.get('email'),
                    phone=new_customer_data.get('phone', ''),
                    address=new_customer_data.get('address', ''),
                    city=new_customer_data.get('city', ''),
                    country=new_customer_data.get('country', ''),
                    created_at=timezone.now()
                )
            
            # ✅ إنشاء الطلب
            order = Order.objects.create(
                customer=customer,
                order_number=validated_data['order_number'],
                total_amount=validated_data['total_amount'],
                status=validated_data['status'],
                payment_method=validated_data.get('payment_method', ''),
                shipping_address=validated_data['shipping_address'],
                notes=validated_data.get('notes', ''),
                created_at=timezone.now()
            )
            
            # ✅ إنشاء عناصر الطلب
            items_data = validated_data.get('items', [])
            
            for item_data in items_data:
                product_id = item_data['product']
                quantity = item_data['quantity']
                price = item_data['price']
                
                # ✅ جلب المنتج
                try:
                    product = Product.objects.get(id=product_id)
                except Product.DoesNotExist:
                    raise serializers.ValidationError(f"Product with id {product_id} does not exist")
                
                # ✅ التحقق من وجود كمية كافية
                if product.quantity < quantity:
                    raise serializers.ValidationError(
                        f"Not enough stock for {product.name}. Available: {product.quantity}, Requested: {quantity}"
                    )
                
                # ✅ ✅ ✅ إنشاء عنصر الطلب فقط - لا نقوم بتحديث الكمية هنا
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=quantity,
                    price=price,
                    sold_at=timezone.now()
                )
                
                # ❌ ❌ ❌ تم إزالة تحديث الكمية من هنا
                # سيتم تحديث الكمية عبر Signal فقط
                
            # ✅ تحديث إحصائيات العميل
            customer.total_orders = Order.objects.filter(customer=customer).count()
            customer.total_spent = Order.objects.filter(
                customer=customer, 
                status='delivered'
            ).aggregate(total=models.Sum('total_amount'))['total'] or 0
            customer.save()
        
        return {
            'customer': CustomerSerializer(customer).data,
            'order': OrderSerializer(order).data
        }