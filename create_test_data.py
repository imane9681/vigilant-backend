# create_test_data.py
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import models
from django.db import transaction
from customers.models import Customer
from products.models import Product, Category
from orders.models import Order, OrderItem
from decimal import Decimal
from datetime import datetime
import random


@transaction.atomic
def create_test_data():
    print("🔄 Creating test data...")
    
    # 1. التأكد من وجود الفئات
    print("\n📂 Checking categories...")
    categories = Category.objects.all()  # ✅ تعريف المتغير هنا
    
    if categories.count() == 0:
        print("❌ No categories found! Please run: python manage.py seed_categories")
        return
    
    print(f"✅ Found {categories.count()} categories")
    for cat in categories:
        print(f"   - {cat.name}")
    
    # 2. إنشاء منتجات من مختلف الفئات
    print("\n📦 Creating products...")
    
    products_data = [
        # Electronics
        {'name': 'iPhone 15 Pro', 'price': 120000, 'quantity': 50, 'category': 'Electronics'},
        {'name': 'MacBook Air M2', 'price': 150000, 'quantity': 30, 'category': 'Electronics'},
        {'name': 'Samsung Galaxy S24', 'price': 100000, 'quantity': 45, 'category': 'Electronics'},
        {'name': 'Sony WH-1000XM5', 'price': 35000, 'quantity': 60, 'category': 'Electronics'},
        
        # Clothing
        {'name': "Levi's Jeans", 'price': 8000, 'quantity': 100, 'category': 'Clothing'},
        {'name': 'Nike Air Max', 'price': 15000, 'quantity': 80, 'category': 'Clothing'},
        {'name': 'Adidas T-Shirt', 'price': 5000, 'quantity': 120, 'category': 'Clothing'},
        {'name': 'Winter Jacket', 'price': 25000, 'quantity': 40, 'category': 'Clothing'},
        
        # Books
        {'name': 'The Great Gatsby', 'price': 2000, 'quantity': 200, 'category': 'Books'},
        {'name': '1984 by Orwell', 'price': 1800, 'quantity': 150, 'category': 'Books'},
        {'name': 'Dune', 'price': 2500, 'quantity': 100, 'category': 'Books'},
        {'name': 'Python Programming', 'price': 4500, 'quantity': 80, 'category': 'Books'},
        
        # Home & Garden
        {'name': 'Wooden Dining Table', 'price': 45000, 'quantity': 20, 'category': 'Home & Garden'},
        {'name': 'Garden Plant Set', 'price': 3000, 'quantity': 150, 'category': 'Home & Garden'},
        {'name': 'LED Floor Lamp', 'price': 12000, 'quantity': 60, 'category': 'Home & Garden'},
        {'name': 'Kitchen Knife Set', 'price': 8000, 'quantity': 70, 'category': 'Home & Garden'},
        
        # Sports
        {'name': 'Football', 'price': 3000, 'quantity': 200, 'category': 'Sports'},
        {'name': 'Yoga Mat', 'price': 2500, 'quantity': 120, 'category': 'Sports'},
        {'name': 'Dumbbell Set 10kg', 'price': 12000, 'quantity': 50, 'category': 'Sports'},
        {'name': 'Tennis Racket', 'price': 8000, 'quantity': 60, 'category': 'Sports'},
        
        # Health & Beauty
        {'name': 'Vitamin C Serum', 'price': 3500, 'quantity': 150, 'category': 'Health & Beauty'},
        {'name': 'Organic Shampoo', 'price': 2000, 'quantity': 200, 'category': 'Health & Beauty'},
        {'name': 'Face Moisturizer', 'price': 2800, 'quantity': 180, 'category': 'Health & Beauty'},
        {'name': 'Protein Powder', 'price': 6000, 'quantity': 100, 'category': 'Health & Beauty'},
        
        # Toys & Games
        {'name': 'LEGO Set', 'price': 4000, 'quantity': 100, 'category': 'Toys & Games'},
        {'name': 'Chess Board', 'price': 3000, 'quantity': 80, 'category': 'Toys & Games'},
        {'name': 'PlayStation 5', 'price': 50000, 'quantity': 30, 'category': 'Toys & Games'},
        {'name': 'Nintendo Switch', 'price': 35000, 'quantity': 40, 'category': 'Toys & Games'},
        
        # Food & Beverages
        {'name': 'Coffee Beans 1kg', 'price': 1500, 'quantity': 300, 'category': 'Food & Beverages'},
        {'name': 'Green Tea 100pcs', 'price': 800, 'quantity': 400, 'category': 'Food & Beverages'},
        {'name': 'Olive Oil 1L', 'price': 1200, 'quantity': 250, 'category': 'Food & Beverages'},
        {'name': 'Honey 500g', 'price': 900, 'quantity': 200, 'category': 'Food & Beverages'},
    ]
    
    # قاموس لتخزين الفئات
    category_map = {cat.name: cat for cat in categories}
    
    products = []
    for p in products_data:
        category = category_map.get(p['category'])
        if not category:
            print(f"⚠️ Category '{p['category']}' not found, skipping...")
            continue
            
        product = Product.objects.create(
            name=p['name'],
            price=Decimal(p['price']),
            quantity=p['quantity'],
            category=category,
            in_stock=True,
            featured=random.choice([True, False])
        )
        products.append(product)
        print(f"✅ Created product: {p['name']} ({p['category']})")
    
    # 3. إنشاء عملاء أساسيين
    print("\n👥 Creating customers...")
    customers = []
    customer_names = [
        'Ahmed Ben Ali', 'Sara Mohamed', 'Khaled Ibrahim', 
        'Nadia Hassan', 'Youssef Omar', 'Lina Ahmed'
    ]
    
    cities = ['Algiers', 'Oran', 'Constantine', 'Annaba', 'Blida', 'Setif']
    
    for i, name in enumerate(customer_names):
        customer = Customer.objects.create(
            name=name,
            email=f'customer{i+1}@example.com',
            phone=f'+213 5{random.randint(10, 99)} {random.randint(100, 999)}',
            address=f'{random.randint(1, 200)} Rue {name.split()[-1]}',
            city=cities[i % len(cities)],
            country='Algeria'
        )
        customers.append(customer)
        print(f"✅ Created customer: {name}")
    
    # 3.5 إضافة عملاء جدد بدون طلبات (لتقليل نسبة التحويل)
    print("\n👥 Creating extra customers (without orders)...")
    extra_customers = [
        {'name': 'Karim Belkacem', 'email': 'karim@example.com', 'city': 'Tizi Ouzou'},
        {'name': 'Fatima Zohra', 'email': 'fatima@example.com', 'city': 'Bejaia'},
        {'name': 'Ali Mansouri', 'email': 'ali@example.com', 'city': 'Tlemcen'},
    ]
    
    for ec in extra_customers:
        customer = Customer.objects.create(
            name=ec['name'],
            email=ec['email'],
            phone=f'+213 5{random.randint(10, 99)} {random.randint(100, 999)}',
            address=f'{random.randint(1, 200)} Rue {ec["name"].split()[-1]}',
            city=ec['city'],
            country='Algeria'
        )
        customers.append(customer)
        print(f"✅ Created customer (no orders): {ec['name']}")
    
    # 4. إنشاء طلبات (13 طلب)
    print("\n📋 Creating orders...")
    order_statuses = ['pending', 'processing', 'shipped', 'delivered', 'delivered', 'delivered']
    payment_methods = ['Credit Card', 'PayPal', 'Bank Transfer', 'Cash on Delivery']
    
    # العملاء الذين سيحصلون على طلبات (6 عملاء فقط)
    customers_with_orders = customers[:6]  # أول 6 عملاء
    
    for i in range(13):
        customer = random.choice(customers_with_orders)
        status = random.choice(order_statuses)
        
        # اختيار 2-4 منتجات عشوائية من مختلف الفئات
        num_items = random.randint(2, 4)
        selected_products = random.sample(products, min(num_items, len(products)))
        
        total = Decimal('0')
        
        # إنشاء الطلب
        order = Order.objects.create(
            order_number=f'ORD-{datetime.now().strftime("%Y%m%d")}-{str(i+1).zfill(4)}',
            customer=customer,
            total_amount=Decimal('0'),
            status=status,
            payment_method=random.choice(payment_methods),
            shipping_address=customer.address,
            notes=f'Test order {i+1}'
        )
        
        # إضافة العناصر
        for product in selected_products:
            quantity = random.randint(1, 3)
            price = product.price
            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=quantity,
                price=price
            )
            total += price * quantity
        
        # تحديث المبلغ الإجمالي
        order.total_amount = total
        order.save()
        
        # تحديث إحصائيات العميل
        customer.total_orders = Order.objects.filter(customer=customer).count()
        customer.total_spent = Order.objects.filter(
            customer=customer, 
            status='delivered'
        ).aggregate(total=models.Sum('total_amount'))['total'] or 0
        customer.save()
        
        # عرض المنتجات في الطلب
        product_names = ', '.join([item.product.name for item in order.items.all()])
        print(f"✅ Created order {i+1}: {customer.name} - ${total} ({product_names})")
    
    print("\n🎉 Test data created successfully!")
    print(f"📂 Categories: {Category.objects.count()}")
    print(f"📦 Products: {Product.objects.count()}")
    print(f"👥 Customers: {Customer.objects.count()}")
    print(f"📋 Orders: {Order.objects.count()}")
    print(f"📝 Order Items: {OrderItem.objects.count()}")
    
    # عرض إحصائيات إضافية
    total_customers = Customer.objects.count()
    customers_with_orders_count = Customer.objects.filter(total_orders__gt=0).count()
    conversion_rate = (customers_with_orders_count / total_customers * 100) if total_customers > 0 else 0
    
    print("\n📊 Conversion Rate Statistics:")
    print(f"   - Total Customers: {total_customers}")
    print(f"   - Customers with orders: {customers_with_orders_count}")
    print(f"   - Conversion Rate: {conversion_rate:.1f}%")


if __name__ == '__main__':
    create_test_data()