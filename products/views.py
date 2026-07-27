# products/views.py
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.db.models import Sum, F, Q
from django.db.models.functions import Coalesce
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.core.files import File
from django.utils import timezone
from datetime import timedelta, datetime
import json
import os
import traceback
import re
import time
import csv
from io import StringIO
from .models import Product, Promotion, Category, Report
from .serializers import ProductSerializer, PromotionSerializer, CategorySerializer, ReportSerializer
from orders.models import OrderItem


class ProductViewSet(viewsets.ModelViewSet):
    """
    ViewSet providing full CRUD operations for products with multiple images support
    """
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [permissions.AllowAny]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    
    def get_queryset(self):
        queryset = Product.objects.all()
        
        name = self.request.query_params.get('name', None)
        if name:
            queryset = queryset.filter(name__icontains=name)
        
        category = self.request.query_params.get('category', None)
        if category:
            queryset = queryset.filter(category=category)
        
        min_price = self.request.query_params.get('min_price', None)
        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        
        max_price = self.request.query_params.get('max_price', None)
        if max_price:
            queryset = queryset.filter(price__lte=max_price)
        
        in_stock = self.request.query_params.get('in_stock', None)
        if in_stock is not None:
            in_stock = in_stock.lower() == 'true'
            queryset = queryset.filter(in_stock=in_stock)
        
        featured = self.request.query_params.get('featured', None)
        if featured is not None:
            featured = featured.lower() == 'true'
            queryset = queryset.filter(featured=featured)
        
        return queryset.order_by('-created_at')
    
    def create(self, request, *args, **kwargs):
        print("\n" + "="*60)
        print("STARTING PRODUCT CREATION")
        print("="*60)
        
        try:
            print("\n📦 POST data:")
            for key, value in request.POST.items():
                print(f"  {key}: {value}")
            
            print("\n📸 FILES received:")
            for key, file in request.FILES.items():
                print(f"  {key}: {file.name} (size: {file.size} bytes, type: {file.content_type})")
            
            data = request.POST.dict()
            print("\n📋 Converted data:", data)
            
            images = request.FILES.getlist('images')
            print(f"\n🖼️ Number of images received: {len(images)}")
            
            image_urls = []
            
            for i, image in enumerate(images):
                print(f"\n--- Processing image {i+1} ---")
                print(f"Filename: {image.name}")
                print(f"Size: {image.size} bytes")
                print(f"Type: {image.content_type}")
                
                try:
                    os.makedirs('media/products', exist_ok=True)
                    clean_name = re.sub(r'[^\w\-_\. ]', '', image.name)
                    clean_name = clean_name.replace(' ', '_')
                    timestamp = int(time.time())
                    name_parts = clean_name.rsplit('.', 1)
                    if len(name_parts) > 1:
                        clean_name = f"{name_parts[0]}_{timestamp}.{name_parts[1]}"
                    else:
                        clean_name = f"{clean_name}_{timestamp}"
                    
                    file_name = f"products/{clean_name}"
                    file_path = default_storage.save(file_name, ContentFile(image.read()))
                    relative_path = file_path
                    image_urls.append(relative_path)
                    print(f"✅ Image saved at: {file_path}")
                    
                except Exception as e:
                    print(f"❌ Error saving image {i+1}: {str(e)}")
                    print(traceback.format_exc())
                    return Response(
                        {'error': f'Failed to save image {i+1}: {str(e)}'},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )
            
            if image_urls:
                try:
                    data['images'] = json.dumps(image_urls)
                    print(f"\n✅ Images converted to JSON: {data['images']}")
                except Exception as e:
                    print(f"❌ Error converting images to JSON: {str(e)}")
                    return Response(
                        {'error': f'Failed to process images: {str(e)}'},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )
            
            if 'tags' in data and data['tags']:
                print(f"\n🏷️ Processing tags: {data['tags']}")
                try:
                    tags = json.loads(data['tags'])
                    data['tags'] = tags
                    print(f"✅ Tags after processing: {tags}")
                except json.JSONDecodeError as e:
                    print(f"Tags are not valid JSON: {e}")
                except Exception as e:
                    print(f"Error processing tags: {str(e)}")
            
            for bool_field in ['featured', 'in_stock']:
                if bool_field in data:
                    data[bool_field] = data[bool_field].lower() == 'true'
                    print(f"✅ Converted {bool_field} to: {data[bool_field]}")

            if 'price' in data:
                if isinstance(data['price'], str):
                    raw = data['price'].strip()
                    if raw != '':
                        data['price'] = raw.replace('،', '.').replace(',', '.')
            if 'weight' in data:
                if isinstance(data['weight'], str):
                    raw = data['weight'].strip()
                    if raw == '':
                        data['weight'] = None
                    else:
                        data['weight'] = raw.replace('،', '.').replace(',', '.')
            if 'quantity' in data and isinstance(data['quantity'], str) and data['quantity'].strip() == '':
                data.pop('quantity', None)
            if 'warranty_months' in data:
                val = data['warranty_months']
                if isinstance(val, str):
                    raw = val.strip()
                    if raw == '':
                        data['warranty_months'] = None
                    else:
                        try:
                            norm = raw.replace('،', '.').replace(',', '.')
                            num = int(float(norm))
                            data['warranty_months'] = num
                        except Exception:
                            data.pop('warranty_months', None)
            
            print("\n📤 Sending data to serializer:", data)
            
            serializer = self.get_serializer(data=data)
            
            if serializer.is_valid():
                print("✅ Data is valid, saving...")
                self.perform_create(serializer)
                instance = serializer.instance
                print(f"✅ Product created with ID: {instance.id}")
                
                if image_urls and instance:
                    try:
                        first_image_path = image_urls[0]
                        full_path = f'media/{first_image_path}'
                        
                        if os.path.exists(full_path):
                            with open(full_path, 'rb') as f:
                                django_file = File(f)
                                filename = os.path.basename(first_image_path)
                                instance.image.save(filename, django_file, save=True)
                                print(f"✅ Main image set to: {instance.image.name}")
                                
                                updated_images = image_urls.copy()
                                seen = set()
                                unique_images = []
                                for img in updated_images:
                                    if img not in seen:
                                        seen.add(img)
                                        unique_images.append(img)
                                
                                instance.images = unique_images
                                instance.save(update_fields=['images'])
                                print(f"✅ Updated images list (unique): {unique_images}")
                        else:
                            print(f"⚠️ Image file not found: {full_path}")
                            
                    except Exception as e:
                        print(f"⚠️ Could not set main image: {str(e)}")
                
                instance.refresh_from_db()
                print("✅ Product creation completed successfully")
                print("="*60 + "\n")
                
                final_serializer = self.get_serializer(instance)
                return Response(final_serializer.data, status=status.HTTP_201_CREATED)
                
            else:
                print("❌ Validation errors:", serializer.errors)
                print("="*60 + "\n")
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            print("🔥 Unexpected error:")
            print(traceback.format_exc())
            print("="*60 + "\n")
            return Response(
                {'error': str(e), 'detail': traceback.format_exc()},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def update(self, request, *args, **kwargs):
        print("\n" + "="*60)
        print("STARTING PRODUCT UPDATE")
        print("="*60)
        
        try:
            instance = self.get_object()
            print(f"📦 Updating product ID: {instance.id}")
            
            print("\n📦 POST data:")
            for key, value in request.POST.items():
                print(f"  {key}: {value}")
            
            print("\n📸 FILES received:")
            for key, file in request.FILES.items():
                print(f"  {key}: {file.name} (size: {file.size} bytes, type: {file.content_type})")
            
            data = request.POST.dict()
            print("\n📋 Converted data:", data)
            
            current_images = []
            if 'images' in data and data['images']:
                try:
                    incoming = json.loads(data['images']) if isinstance(data['images'], str) else data['images']
                    if isinstance(incoming, list):
                        current_images = [img for img in incoming if img]
                    else:
                        current_images = []
                    print(f"\n🖼️ Incoming images from POST (final list): {current_images}")
                except Exception as e:
                    print(f"⚠️ Failed to parse incoming images: {e}")
                    current_images = []
            else:
                if instance.images:
                    if isinstance(instance.images, str):
                        try:
                            current_images = json.loads(instance.images)
                        except:
                            current_images = []
                    elif isinstance(instance.images, list):
                        current_images = instance.images

            current_images = list(dict.fromkeys(current_images))
            print(f"\n🖼️ Current images base (unique): {current_images}")

            new_images = request.FILES.getlist('images')
            print(f"\n📸 Number of uploaded new images: {len(new_images)}")

            if new_images:
                for i, image in enumerate(new_images):
                    print(f"\n--- Processing new image {i+1} ---")
                    print(f"Filename: {image.name}")
                    try:
                        os.makedirs('media/products', exist_ok=True)
                        clean_name = re.sub(r'[^\w\-_\. ]', '', image.name)
                        clean_name = clean_name.replace(' ', '_')
                        timestamp = int(time.time())
                        name_parts = clean_name.rsplit('.', 1)
                        if len(name_parts) > 1:
                            clean_name = f"{name_parts[0]}_{timestamp}.{name_parts[1]}"
                        else:
                            clean_name = f"{clean_name}_{timestamp}"
                        file_name = f"products/{clean_name}"
                        file_path = default_storage.save(file_name, ContentFile(image.read()))
                        current_images.append(file_path)
                        print(f"✅ New image saved at: {file_path}")
                    except Exception as e:
                        print(f"❌ Error saving new image {i+1}: {str(e)}")
                        return Response(
                            {'error': f'Failed to save new image {i+1}: {str(e)}'},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR
                        )

            current_images = list(dict.fromkeys(current_images))
            print(f"\n📸 Final images list to save (unique): {current_images}")
            data['images'] = json.dumps(current_images)

            if 'tags' in data:
                value = data['tags']
                try:
                    tags_list = json.loads(value) if isinstance(value, str) else value
                    if isinstance(tags_list, list):
                        data['tags'] = json.dumps(tags_list)
                        print(f"✅ Tags normalized to JSON string: {data['tags']}")
                    else:
                        if isinstance(value, str):
                            parts = [t.strip() for t in value.split(',') if t.strip()]
                            data['tags'] = json.dumps(parts)
                            print(f"✅ Tags parsed from CSV to JSON string: {data['tags']}")
                except Exception as e:
                    print(f"⚠️ Could not normalize tags, keeping as is. Error: {e}")
            
            for bool_field in ['featured', 'in_stock']:
                if bool_field in data:
                    data[bool_field] = data[bool_field].lower() == 'true'
                    print(f"✅ Converted {bool_field} to: {data[bool_field]}")

            if 'price' in data:
                if isinstance(data['price'], str):
                    raw = data['price'].strip()
                    if raw == '':
                        data.pop('price', None)
                    else:
                        data['price'] = raw.replace('،', '.').replace(',', '.')
            if 'weight' in data:
                if isinstance(data['weight'], str):
                    raw = data['weight'].strip()
                    if raw == '':
                        data['weight'] = None
                    else:
                        data['weight'] = raw.replace('،', '.').replace(',', '.')
            if 'quantity' in data and isinstance(data['quantity'], str):
                if data['quantity'].strip() == '':
                    data.pop('quantity', None)
            if 'warranty_months' in data:
                val = data['warranty_months']
                if isinstance(val, str):
                    raw = val.strip()
                    if raw == '':
                        data['warranty_months'] = None
                    else:
                        try:
                            norm = raw.replace('،', '.').replace(',', '.')
                            num = int(float(norm))
                            data['warranty_months'] = num
                        except Exception:
                            data.pop('warranty_months', None)
            
            print("\n📤 Sending update data to serializer:", data)
            
            serializer = self.get_serializer(instance, data=data, partial=True)
            
            if serializer.is_valid():
                print("✅ Update data is valid, saving...")
                self.perform_update(serializer)
                
                if new_images and current_images:
                    try:
                        first_image_path = current_images[0]
                        full_path = f'media/{first_image_path}'
                        
                        if os.path.exists(full_path):
                            with open(full_path, 'rb') as f:
                                django_file = File(f)
                                filename = os.path.basename(first_image_path)
                                instance.image.save(filename, django_file, save=True)
                                print(f"✅ Main image updated to: {instance.image.name}")
                                
                                updated_images = current_images.copy()
                                seen = set()
                                unique_images = []
                                for img in updated_images:
                                    if img not in seen:
                                        seen.add(img)
                                        unique_images.append(img)
                                
                                instance.images = unique_images
                                instance.save(update_fields=['images'])
                    except Exception as e:
                        print(f"⚠️ Could not update main image: {str(e)}")
                
                instance.refresh_from_db()
                print("✅ Product updated successfully")
                print("="*60 + "\n")
                
                final_serializer = self.get_serializer(instance)
                return Response(final_serializer.data)
            else:
                print("❌ Validation errors:", serializer.errors)
                print("="*60 + "\n")
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            print("🔥 Unexpected error in update:")
            print(traceback.format_exc())
            print("="*60 + "\n")
            return Response(
                {'error': str(e), 'detail': traceback.format_exc()},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            print(f"\n🗑️ Deleting product ID: {instance.id}")
            
            if instance.images:
                images = []
                if isinstance(instance.images, str):
                    try:
                        images = json.loads(instance.images)
                    except:
                        images = []
                elif isinstance(instance.images, list):
                    images = instance.images
                
                for image_path in images:
                    try:
                        if image_path:
                            if default_storage.exists(image_path):
                                default_storage.delete(image_path)
                                print(f"✅ Deleted image: {image_path}")
                    except Exception as e:
                        print(f"⚠️ Could not delete image {image_path}: {str(e)}")
            
            if instance.image and instance.image.name:
                try:
                    if default_storage.exists(instance.image.name):
                        default_storage.delete(instance.image.name)
                        print(f"✅ Deleted main image: {instance.image.name}")
                except Exception as e:
                    print(f"⚠️ Could not delete main image: {str(e)}")
            
            self.perform_destroy(instance)
            print("✅ Product deleted successfully")
            print("="*60 + "\n")
            
            return Response(status=status.HTTP_204_NO_CONTENT)
            
        except Exception as e:
            print(f"🔥 Error deleting product: {str(e)}")
            print(traceback.format_exc())
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        try:
            total_products = Product.objects.count()
            agg_qty = Product.objects.aggregate(total=Coalesce(Sum('quantity'), 0))
            total_quantity = agg_qty.get('total') or 0
            agg_val = Product.objects.aggregate(total=Coalesce(Sum(F('price') * F('quantity')), 0))
            total_value = agg_val.get('total') or 0
            
            categories = {}
            for category in Product.objects.values_list('category', flat=True).distinct():
                if category:
                    count = Product.objects.filter(category=category).count()
                    categories[category] = count
            
            return Response({
                'total_products': int(total_products),
                'total_quantity': int(total_quantity or 0),
                'total_value': float(total_value or 0),
                'categories': categories,
            })
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def update_quantity(self, request, pk=None):
        try:
            product = self.get_object()
            quantity = request.data.get('quantity')
            
            if quantity is None:
                return Response(
                    {'error': 'Quantity is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            try:
                quantity = int(quantity)
            except (ValueError, TypeError):
                return Response(
                    {'error': 'Quantity must be a number'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if quantity < 0:
                return Response(
                    {'error': 'Quantity cannot be negative'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            product.quantity = quantity
            product.save()
            
            serializer = self.get_serializer(product)
            return Response(serializer.data)
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['delete'])
    def delete_image(self, request, pk=None):
        try:
            product = self.get_object()
            image_index = request.data.get('index')
            image_url = request.data.get('image_url')
            
            if image_index is None and image_url is None:
                return Response(
                    {'error': 'Please specify which image to delete'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            current_images = []
            if product.images:
                if isinstance(product.images, str):
                    try:
                        current_images = json.loads(product.images)
                    except:
                        current_images = []
                elif isinstance(product.images, list):
                    current_images = product.images
            
            current_images = list(dict.fromkeys(current_images))
            
            removed_image = None
            if image_index is not None and 0 <= image_index < len(current_images):
                removed_image = current_images.pop(image_index)
                print(f"Removing image at index {image_index}: {removed_image}")
                
            elif image_url and image_url in current_images:
                current_images.remove(image_url)
                removed_image = image_url
                print(f"Removing image: {removed_image}")
            
            if removed_image:
                if default_storage.exists(removed_image):
                    default_storage.delete(removed_image)
                    print(f"✅ Deleted file: {removed_image}")
            
            product.images = current_images
            
            if product.image and removed_image and product.image.name == removed_image:
                if current_images:
                    first_image_path = current_images[0]
                    full_path = f'media/{first_image_path}'
                    if os.path.exists(full_path):
                        with open(full_path, 'rb') as f:
                            django_file = File(f)
                            filename = os.path.basename(first_image_path)
                            product.image.save(filename, django_file, save=True)
                else:
                    product.image = None
            
            product.save()
            
            serializer = self.get_serializer(product)
            return Response(serializer.data)
            
        except Exception as e:
            print(f"Error deleting image: {str(e)}")
            print(traceback.format_exc())
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    # ============================================
    # ✅ ✅ ✅ الدالة الرئيسية المحسنة
    # ============================================
    
    @action(detail=False, methods=['get'])
    def top_selling_with_growth(self, request):
        """
        ✅ الحصول على أفضل المنتجات مبيعاً مع نسبة النمو
        - محسوب من مبيعات الشهر الحالي والشهر الماضي
        """
        try:
            from orders.models import OrderItem
            from django.utils import timezone
            from datetime import timedelta
            
            limit = int(request.query_params.get('limit', 5))
            
            print("=" * 60)
            print("📊 Calculating Top Selling Products with Growth")
            print("=" * 60)
            
            # ✅ حساب إجمالي المبيعات لكل منتج
            product_sales = OrderItem.objects.values('product_id').annotate(
                total_sold=Sum('quantity')
            ).order_by('-total_sold')[:limit]
            
            product_ids = [item['product_id'] for item in product_sales if item['product_id']]
            
            if not product_ids:
                print("⚠️ No products found with sales")
                return Response([])
            
            products = Product.objects.filter(id__in=product_ids)
            
            # ✅ تعريف الفترات الزمنية
            now = timezone.now()
            current_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            last_month_start = (current_month_start - timedelta(days=1)).replace(day=1)
            last_month_end = current_month_start - timedelta(seconds=1)
            
            print(f"📅 Current month start: {current_month_start}")
            print(f"📅 Last month start: {last_month_start}")
            print(f"📅 Last month end: {last_month_end}")
            
            result = []
            
            for product in products:
                # ✅ ✅ ✅ مبيعات الشهر الحالي
                current_sales = OrderItem.objects.filter(
                    product=product,
                    sold_at__gte=current_month_start,
                    sold_at__lt=now
                ).aggregate(total=Sum('quantity'))['total'] or 0
                
                # ✅ ✅ ✅ مبيعات الشهر الماضي
                previous_sales = OrderItem.objects.filter(
                    product=product,
                    sold_at__gte=last_month_start,
                    sold_at__lt=current_month_start
                ).aggregate(total=Sum('quantity'))['total'] or 0
                
                # ✅ ✅ ✅ إجمالي المبيعات (كل الوقت)
                total_sold = OrderItem.objects.filter(
                    product=product
                ).aggregate(total=Sum('quantity'))['total'] or 0
                
                # ✅ ✅ ✅ حساب نسبة النمو
                if previous_sales > 0:
                    growth = ((current_sales - previous_sales) / previous_sales) * 100
                else:
                    if current_sales > 0:
                        growth = 100.0
                    else:
                        growth = 0.0
                
                # ✅ ✅ ✅ حساب الإيرادات
                revenue = float(product.price) * total_sold if product.price else 0
                
                # ✅ الحصول على اسم الفئة
                category_name = product.category.name if product.category else None
                
                # ✅ الحصول على صورة المنتج
                image_url = None
                if product.image and product.image.name:
                    image_url = f"/media/{product.image.name}"
                elif product.images and len(product.images) > 0:
                    if isinstance(product.images, list):
                        image_url = f"/media/{product.images[0]}"
                    elif isinstance(product.images, str):
                        try:
                            images_list = json.loads(product.images)
                            if images_list and len(images_list) > 0:
                                image_url = f"/media/{images_list[0]}"
                        except:
                            pass
                
                # ✅ ✅ ✅ طباعة البيانات للتشخيص
                print(f"\n📊 Product: {product.name}")
                print(f"   Current sales: {current_sales}")
                print(f"   Previous sales: {previous_sales}")
                print(f"   Growth: {growth:.1f}%")
                print(f"   Total sold: {total_sold}")
                print(f"   Revenue: ${revenue:,.2f}")
                
                result.append({
                    'id': product.id,
                    'name': product.name,
                    'price': float(product.price) if product.price else 0,
                    'quantity': product.quantity,
                    'category': category_name,
                    'image': image_url,
                    'images': product.images,
                    'sold_count': total_sold,
                    'growth': round(growth, 1),
                    'current_sales': current_sales,
                    'previous_sales': previous_sales,
                    'revenue': revenue,
                    'stock': product.quantity,
                    'supplier': product.manufacturer or 'Unknown',
                    'sku': product.sku or f'SKU-{product.id}',
                    'description': product.description or '',
                    'manufacturer': product.manufacturer or '',
                    'weight': product.weight or '',
                    'dimensions': product.dimensions or '',
                    'warranty_months': product.warranty_months or '',
                    'tags': product.tags or '',
                    'featured': product.featured or False,
                    'images_list': product.images or []
                })
            
            # ✅ ترتيب حسب إجمالي المبيعات
            result.sort(key=lambda x: x['sold_count'], reverse=True)
            
            print(f"\n✅ Returning {len(result)} products")
            print("=" * 60)
            
            return Response(result[:limit])
            
        except Exception as e:
            print(f"❌ Error in top_selling_with_growth: {str(e)}")
            import traceback
            traceback.print_exc()
            return Response({'error': str(e)}, status=500)
    
    # ============================================
    # ✅ ✅ ✅ دالة إعادة الطلب
    # ============================================
    
    @action(detail=True, methods=['post'])
    def reorder(self, request, pk=None):
        """
        ✅ إعادة طلب منتج معين
        """
        try:
            product = self.get_object()
            quantity = request.data.get('quantity', 10)
            supplier = request.data.get('supplier', '')
            priority = request.data.get('priority', 'medium')
            notes = request.data.get('notes', '')
            
            reorder_data = {
                'product_id': product.id,
                'product_name': product.name,
                'quantity': quantity,
                'supplier': supplier,
                'priority': priority,
                'notes': notes,
                'ordered_at': timezone.now().isoformat()
            }
            
            print(f"📦 Reorder placed for {product.name}: {quantity} units from {supplier}")
            print(f"📝 Notes: {notes}")
            print(f"📊 Priority: {priority}")
            
            return Response({
                'success': True,
                'message': f'Reorder placed successfully for {product.name}',
                'reorder': reorder_data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            print(f"❌ Error in reorder: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# ========== PROMOTION VIEWSET ==========
class PromotionViewSet(viewsets.ModelViewSet):
    queryset = Promotion.objects.all()
    serializer_class = PromotionSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        queryset = Promotion.objects.all()
        status_filter = self.request.query_params.get('status', None)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        is_active = self.request.query_params.get('is_active', None)
        if is_active == 'true':
            now = timezone.now()
            queryset = queryset.filter(start_date__lte=now, end_date__gte=now, status='active')
        
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | Q(code__icontains=search)
            )
        
        return queryset.order_by('-created_at')
    
    @action(detail=True, methods=['post'])
    def apply(self, request, pk=None):
        promotion = self.get_object()
        order_total = request.data.get('order_total', 0)
        
        if not promotion.is_active:
            return Response(
                {'error': 'Promotion is not active'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if promotion.used_count >= promotion.max_uses:
            return Response(
                {'error': 'Promotion has reached maximum uses'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if order_total < promotion.min_purchase:
            return Response({
                'error': f'Minimum purchase of ${promotion.min_purchase} required',
                'min_purchase': float(promotion.min_purchase)
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if promotion.discount_type == 'percentage':
            discount = (promotion.discount_value / 100) * order_total
            if promotion.max_discount:
                discount = min(discount, promotion.max_discount)
        elif promotion.discount_type == 'fixed':
            discount = min(promotion.discount_value, order_total)
        else:
            discount = 0
        
        return Response({
            'discount': float(discount),
            'new_total': float(order_total - discount),
            'promotion_code': promotion.code,
            'promotion_name': promotion.name,
            'message': f'Applied {promotion.get_discount_display()}'
        })
    
    @action(detail=True, methods=['post'])
    def increment_usage(self, request, pk=None):
        promotion = self.get_object()
        promotion.used_count += 1
        promotion.total_uses += 1
        revenue = request.data.get('revenue_generated', 0)
        promotion.revenue_generated += revenue
        promotion.save()
        
        return Response({
            'used_count': promotion.used_count,
            'remaining_uses': promotion.max_uses - promotion.used_count,
            'total_uses': promotion.total_uses
        })
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        total = Promotion.objects.count()
        active = Promotion.objects.filter(status='active').count()
        scheduled = Promotion.objects.filter(status='scheduled').count()
        expired = Promotion.objects.filter(status='expired').count()
        
        total_uses = Promotion.objects.aggregate(total=Sum('total_uses'))['total'] or 0
        total_revenue = Promotion.objects.aggregate(total=Sum('revenue_generated'))['total'] or 0
        
        return Response({
            'total': total,
            'active': active,
            'scheduled': scheduled,
            'expired': expired,
            'total_uses': total_uses,
            'total_revenue': total_revenue
        })


# ========== REPORT VIEWSET ==========
class ReportViewSet(viewsets.ModelViewSet):
    queryset = Report.objects.all()
    serializer_class = ReportSerializer
    permission_classes = [permissions.AllowAny]
    
    @action(detail=False, methods=['post'])
    def generate(self, request):
        report_type = request.data.get('type', 'sales')
        report_format = request.data.get('format', 'csv')
        date_range = request.data.get('date_range', 'month')
        start_date = request.data.get('start_date')
        end_date = request.data.get('end_date')
        
        if report_type == 'sales':
            content = self.generate_sales_report(date_range, start_date, end_date)
        elif report_type == 'inventory':
            content = self.generate_inventory_report()
        elif report_type == 'customers':
            content = self.generate_customers_report()
        elif report_type == 'financial':
            content = self.generate_financial_report()
        else:
            content = self.generate_products_report()
        
        filename = f"{report_type}_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{report_format}"
        file_content = ContentFile(content.encode('utf-8'))
        
        report = Report.objects.create(
            title=f"{report_type.capitalize()} Report",
            type=report_type,
            format=report_format,
            file_size=len(content),
            date_range_start=start_date,
            date_range_end=end_date
        )
        report.file.save(filename, file_content, save=True)
        
        serializer = self.get_serializer(report)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        report = self.get_object()
        report.download_count += 1
        report.save()
        
        if report.file:
            response = Response()
            response['Content-Disposition'] = f'attachment; filename="{report.file.name.split("/")[-1]}"'
            response['Content-Type'] = 'application/octet-stream'
            response.content = report.file.read()
            return response
        return Response({'error': 'File not found'}, status=status.HTTP_404_NOT_FOUND)
        
    @action(detail=True, methods=['post'])
    def increment_download(self, request, pk=None):
        report = self.get_object()
        report.download_count += 1
        report.save()
        return Response({
            'id': report.id,
            'download_count': report.download_count
        })

    
    def generate_sales_report(self, date_range, start_date, end_date):
        from orders.models import Order
        
        orders = Order.objects.all()
        if start_date and end_date:
            orders = orders.filter(created_at__date__gte=start_date, created_at__date__lte=end_date)
        
        total_revenue = sum(float(o.total_amount) for o in orders)
        
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(['Sales Report', f'Generated: {datetime.now().strftime("%Y-%m-%d %H:%M")}'])
        writer.writerow([])
        writer.writerow(['Total Revenue', f'${total_revenue:,.2f}'])
        writer.writerow(['Total Orders', orders.count()])
        writer.writerow([])
        writer.writerow(['Order ID', 'Customer', 'Amount', 'Status', 'Date'])
        
        for order in orders[:100]:
            writer.writerow([
                order.order_number,
                order.customer.name,
                f'${float(order.total_amount):,.2f}',
                order.status,
                order.created_at.strftime('%Y-%m-%d')
            ])
        
        return output.getvalue()
    
    def generate_inventory_report(self):
        products = Product.objects.all()
        
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(['Inventory Report', f'Generated: {datetime.now().strftime("%Y-%m-%d %H:%M")}'])
        writer.writerow([])
        writer.writerow(['Total Products', products.count()])
        writer.writerow(['Total Value', f'${sum(float(p.price) * (p.quantity or 0) for p in products):,.2f}'])
        writer.writerow(['Low Stock', products.filter(quantity__lte=10, quantity__gt=0).count()])
        writer.writerow(['Out of Stock', products.filter(quantity=0).count()])
        writer.writerow([])
        writer.writerow(['Product Name', 'SKU', 'Quantity', 'Price', 'Value'])
        
        for product in products:
            writer.writerow([
                product.name,
                product.sku or 'N/A',
                product.quantity or 0,
                f'${float(product.price):,.2f}',
                f'${float(product.price) * (product.quantity or 0):,.2f}'
            ])
        
        return output.getvalue()
    
    def generate_customers_report(self):
        from orders.models import Customer
        
        customers = Customer.objects.all()
        
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(['Customers Report', f'Generated: {datetime.now().strftime("%Y-%m-%d %H:%M")}'])
        writer.writerow([])
        writer.writerow(['Total Customers', customers.count()])
        writer.writerow([])
        writer.writerow(['Name', 'Email', 'Phone', 'Total Orders', 'Total Spent', 'Joined'])
        
        for customer in customers:
            writer.writerow([
                customer.name,
                customer.email,
                customer.phone or 'N/A',
                customer.total_orders,
                f'${float(customer.total_spent):,.2f}',
                customer.created_at.strftime('%Y-%m-%d') if customer.created_at else 'N/A'
            ])
        
        return output.getvalue()
    
    def generate_financial_report(self):
        from orders.models import Order, Customer
        
        orders = Order.objects.all()
        customers = Customer.objects.all()
        products = Product.objects.all()
        
        total_revenue = sum(float(o.total_amount) for o in orders)
        inventory_value = sum(float(p.price) * (p.quantity or 0) for p in products)
        
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(['Financial Report', f'Generated: {datetime.now().strftime("%Y-%m-%d %H:%M")}'])
        writer.writerow([])
        writer.writerow(['Total Revenue', f'${total_revenue:,.2f}'])
        writer.writerow(['Total Orders', orders.count()])
        writer.writerow(['Total Customers', customers.count()])
        writer.writerow(['Inventory Value', f'${inventory_value:,.2f}'])
        writer.writerow(['Average Order Value', f'${total_revenue / max(orders.count(), 1):,.2f}'])
        
        return output.getvalue()
    
    def generate_products_report(self):
        products = Product.objects.all()
        
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(['Products Report', f'Generated: {datetime.now().strftime("%Y-%m-%d %H:%M")}'])
        writer.writerow([])
        writer.writerow(['Total Products', products.count()])
        writer.writerow([])
        writer.writerow(['Product Name', 'Category', 'Price', 'Stock', 'Status'])
        
        for product in products:
            status = 'In Stock'
            if product.quantity == 0:
                status = 'Out of Stock'
            elif product.quantity <= 10:
                status = 'Low Stock'
            
            writer.writerow([
                product.name,
                product.category.name if product.category else 'Uncategorized',
                f'${float(product.price):,.2f}',
                product.quantity or 0,
                status
            ])
        
        return output.getvalue()


# ========== CATEGORY VIEWSET ==========
class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        queryset = Category.objects.all()
        
        is_active = self.request.query_params.get('is_active', None)
        if is_active is not None:
            is_active = is_active.lower() == 'true'
            queryset = queryset.filter(is_active=is_active)
        
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(name__icontains=search)
        
        return queryset.order_by('name')
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        total = Category.objects.count()
        active = Category.objects.filter(is_active=True).count()
        
        return Response({
            'total': total,
            'active': active
        })