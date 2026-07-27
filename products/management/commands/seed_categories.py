from django.core.management.base import BaseCommand
from products.models import Category

class Command(BaseCommand):
    help = 'Seed initial categories with default data'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('🚀 Seeding categories...'))
        
        categories_data = [
            {'name': 'Electronics', 'description': 'Electronic devices and gadgets', 'icon': 'Laptop', 'color': '#8B7ABA', 'is_active': True},
            {'name': 'Clothing', 'description': 'Apparel and fashion items', 'icon': 'Shirt', 'color': '#F08FAE', 'is_active': True},
            {'name': 'Books', 'description': 'Books and publications', 'icon': 'BookOpen', 'color': '#34D19C', 'is_active': True},
            {'name': 'Home & Garden', 'description': 'Home decor and garden items', 'icon': 'Home', 'color': '#EE9C6C', 'is_active': True},
            {'name': 'Sports', 'description': 'Sports equipment and gear', 'icon': 'Dumbbell', 'color': '#3B82F6', 'is_active': True},
            {'name': 'Health & Beauty', 'description': 'Health and beauty products', 'icon': 'Heart', 'color': '#EC4899', 'is_active': True},
            {'name': 'Toys & Games', 'description': 'Toys and games', 'icon': 'Gamepad2', 'color': '#F59E0B', 'is_active': True},
            {'name': 'Food & Beverages', 'description': 'Food and beverages', 'icon': 'Coffee', 'color': '#10B981', 'is_active': True}
        ]

        created_count = 0
        existing_count = 0

        for cat_data in categories_data:
            category, created = Category.objects.get_or_create(
                name=cat_data['name'],
                defaults={
                    'description': cat_data['description'],
                    'icon': cat_data['icon'],
                    'color': cat_data['color'],
                    'is_active': cat_data['is_active']
                }
            )
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f"✅ تم إنشاء: {category.name}"))
            else:
                existing_count += 1
                self.stdout.write(self.style.WARNING(f"⏩ موجود بالفعل: {category.name}"))

        self.stdout.write('-' * 60)
        self.stdout.write(self.style.SUCCESS(f"📊 تم إنشاء {created_count} فئة جديدة"))
        self.stdout.write(self.style.SUCCESS(f"📦 إجمالي الفئات: {Category.objects.count()}"))
        self.stdout.write('-' * 60)