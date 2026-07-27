# products/models.py
from django.db import models



class Product(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.IntegerField(default=0)
    
    # ✅ الحقل القديم (نحتفظ به مؤقتاً)
    category_old = models.CharField(max_length=100, blank=True, null=True)
    
    # ✅ الحقل الجديد (ForeignKey)
    category = models.ForeignKey(
        'Category', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='products'
    )
    
    # Multiple images field - stores image paths as JSON
    images = models.JSONField(default=list, blank=True, null=True)
    
    # Keep the old image field for backward compatibility
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    # New fields
    sku = models.CharField(max_length=50, blank=True, null=True)
    weight = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    dimensions = models.CharField(max_length=100, blank=True, null=True)
    manufacturer = models.CharField(max_length=100, blank=True, null=True)
    warranty_months = models.IntegerField(blank=True, null=True)
    tags = models.CharField(max_length=200, blank=True, null=True)
    featured = models.BooleanField(default=False)
    in_stock = models.BooleanField(default=True)
    sold_count = models.IntegerField(default=0)
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Product'
        verbose_name_plural = 'Products'



class Promotion(models.Model):
    """نموذج العروض والخصومات"""
    DISCOUNT_TYPE_CHOICES = [
        ('percentage', 'Percentage (%)'),
        ('fixed', 'Fixed Amount ($)'),
        ('free_shipping', 'Free Shipping'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('scheduled', 'Scheduled'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
    ]
    
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True, null=True)
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPE_CHOICES, default='percentage')
    discount_value = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # الشروط
    min_purchase = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    max_discount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    max_uses = models.IntegerField(default=1000)
    used_count = models.IntegerField(default=0)
    
    # التواريخ
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    
    # الحالة
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    # لمنتجات محددة (اختياري)
    applicable_products = models.ManyToManyField('Product', blank=True, related_name='promotions')
    applicable_categories = models.JSONField(default=list, blank=True, null=True)
    
    # إحصائيات
    total_uses = models.IntegerField(default=0)
    revenue_generated = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.code})"
    
    @property
    def is_active(self):
        from django.utils import timezone
        now = timezone.now()
        return self.start_date <= now <= self.end_date and self.status == 'active'
    
    @property
    def usage_percentage(self):
        if self.max_uses > 0:
            return (self.total_uses / self.max_uses) * 100
        return 0
    
    class Meta:
        ordering = ['-created_at']


class Report(models.Model):
    """نموذج التقارير المخزنة"""
    REPORT_TYPES = [
        ('sales', 'Sales Report'),
        ('inventory', 'Inventory Report'),
        ('customers', 'Customers Report'),
        ('financial', 'Financial Report'),
        ('products', 'Products Report'),
    ]
    
    FORMAT_TYPES = [
        ('pdf', 'PDF'),
        ('excel', 'Excel'),
        ('csv', 'CSV'),
    ]
    
    title = models.CharField(max_length=200)
    type = models.CharField(max_length=20, choices=REPORT_TYPES)
    format = models.CharField(max_length=10, choices=FORMAT_TYPES, default='csv')
    file = models.FileField(upload_to='reports/', null=True, blank=True)
    file_size = models.IntegerField(default=0)
    download_count = models.IntegerField(default=0)
    status = models.CharField(max_length=20, default='generated')
    date_range_start = models.DateField(null=True, blank=True)
    date_range_end = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.title} - {self.created_at.strftime('%Y-%m-%d')}"
    
    @property
    def size_display(self):
        if self.file_size < 1024:
            return f"{self.file_size} B"
        elif self.file_size < 1024 * 1024:
            return f"{self.file_size / 1024:.1f} KB"
        else:
            return f"{self.file_size / (1024 * 1024):.1f} MB"
    
    class Meta:
        ordering = ['-created_at']


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    icon = models.CharField(max_length=50, blank=True, null=True)
    color = models.CharField(max_length=20, default='primary')
    is_active = models.BooleanField(default=True)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='subcategories')  # ✅ هذا مهم
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'