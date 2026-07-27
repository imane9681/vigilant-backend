# products/admin.py
from django.contrib import admin
from .models import Product
from .models import Product, Category

import json

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'price', 'quantity', 'category', 'image_count', 'featured', 'in_stock', 'created_at']
    list_filter = ['category', 'featured', 'in_stock', 'created_at']
    search_fields = ['name', 'description', 'sku']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'image_preview', 'image_list_preview']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'price', 'quantity', 'sku')
        }),
        ('Categories & Tags', {
            'fields': ('category', 'tags', 'featured', 'in_stock')
        }),
        ('Images', {
            'fields': ('image', 'images', 'image_preview', 'image_list_preview')
        }),
        ('Specifications', {
            'fields': ('weight', 'dimensions', 'manufacturer', 'warranty_months')
        }),
        ('Metadata', {
            'fields': ('created_at',)
        }),
    )
    
    def image_count(self, obj):
        """Display image count in admin panel"""
        if obj.images:
            if isinstance(obj.images, str):
                try:
                    images = json.loads(obj.images)
                    return len(images)
                except:
                    return 0
            elif isinstance(obj.images, list):
                return len(obj.images)
        return 0
    image_count.short_description = 'Image Count'
    
    def image_preview(self, obj):
        """Preview main image in admin panel"""
        if obj.image and obj.image.name:
            return f'<img src="{obj.image.url}" style="max-height: 100px; max-width: 100px;" />'
        return "No main image"
    image_preview.allow_tags = True
    image_preview.short_description = 'Main Image Preview'
    
    def image_list_preview(self, obj):
        """Preview all images in admin panel"""
        if obj.images:
            images = []
            if isinstance(obj.images, str):
                try:
                    images = json.loads(obj.images)
                except:
                    images = []
            elif isinstance(obj.images, list):
                images = obj.images
            
            if images:
                html = '<div style="display: flex; gap: 5px; flex-wrap: wrap;">'
                for img in images[:5]:  # Show first 5 images
                    html += f'<img src="{img}" style="max-height: 50px; max-width: 50px;" />'
                if len(images) > 5:
                    html += f'<span>+{len(images)-5} more</span>'
                html += '</div>'
                return html
        return "No images"
    image_list_preview.allow_tags = True
    image_list_preview.short_description = 'All Images Preview'


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'parent', 'is_active', 'created_at']
    list_filter = ['is_active', 'parent']
    search_fields = ['name', 'description']
    ordering = ['name']