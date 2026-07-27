# products/serializers.py
from rest_framework import serializers
from .models import Product, Promotion
from .models import Product, Promotion, Report
from .models import Product, Promotion, Category
import json

class ProductSerializer(serializers.ModelSerializer):
    """
    Serializer for Product model with multiple images support
    """
    
    # Make image field read-only
    image = serializers.ImageField(read_only=True)
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'description', 'price', 'quantity', 
            'category', 'image', 'images', 'created_at', 'sku', 'weight',
            'dimensions', 'manufacturer', 'warranty_months', 
            'tags', 'featured', 'in_stock' , 'sold_count'
        ]
        read_only_fields = ['id', 'created_at', 'image']
    
    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("Price must be greater than zero")
        return value
    
    def validate_quantity(self, value):
        if value < 0:
            raise serializers.ValidationError("Quantity cannot be negative")
        return value
    
    def to_representation(self, instance):
        """Format data when sending to frontend"""
        data = super().to_representation(instance)
        
        # Handle images field
        if instance.images:
            image_list = []
            
            if isinstance(instance.images, str):
                try:
                    image_list = json.loads(instance.images)
                except:
                    image_list = []
            elif isinstance(instance.images, list):
                image_list = instance.images
            
            data['images'] = [f"/media/{img}" for img in image_list if img]
        else:
            data['images'] = []
        
        # Handle image field
        if instance.image and instance.image.name:
            data['image'] = f"/media/{instance.image.name}"
        else:
            data['image'] = None
        
        # Handle tags field
        if instance.tags:
            if isinstance(instance.tags, str):
                try:
                    data['tags'] = json.loads(instance.tags)
                except:
                    if ',' in instance.tags:
                        data['tags'] = [tag.strip() for tag in instance.tags.split(',')]
                    else:
                        data['tags'] = instance.tags
            else:
                data['tags'] = instance.tags
        else:
            data['tags'] = []
        
        return data


class PromotionSerializer(serializers.ModelSerializer):
    is_active = serializers.BooleanField(read_only=True)
    usage_percentage = serializers.FloatField(read_only=True)
    discount_display = serializers.SerializerMethodField()
    
    class Meta:
        model = Promotion
        fields = '__all__'
    
    def get_discount_display(self, obj):
        if obj.discount_type == 'percentage':
            return f"{obj.discount_value}% OFF"
        elif obj.discount_type == 'fixed':
            return f"${obj.discount_value} OFF"
        return "Free Shipping"


class ReportSerializer(serializers.ModelSerializer):
    size_display = serializers.CharField(read_only=True)
    
    class Meta:
        model = Report
        fields = ['id', 'title', 'type', 'format', 'file', 'file_size', 'size_display', 
                  'download_count', 'status', 'date_range_start', 'date_range_end', 'created_at']
        read_only_fields = ['id', 'created_at', 'file', 'file_size', 'download_count']


class CategorySerializer(serializers.ModelSerializer):
    """Serializer for Category model"""
    product_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'icon', 'color', 'is_active', 'parent', 'product_count', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_product_count(self, obj):
        """Count products in this category"""
        from .models import Product
        # ✅ استخدم obj.id لتصفية المنتجات
        return Product.objects.filter(category_id=obj.id).count()