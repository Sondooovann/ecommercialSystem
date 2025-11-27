import logging
import random

import cloudinary.uploader
from django.core.paginator import PageNotAnInteger
from django.utils.text import slugify
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.parsers import MultiPartParser, FormParser
from core.permission import IsShopOwner, IsActiveUser
from core.views import IsAdminUser
from shops.models import Shop
from .models import (
    Product, ProductImage, ProductVariant,
    Attribute, AttributeValue, VariantAttributeValue,
    Tag, ProductTag, Category, Brand
)
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from orders.models import OrderItem
import time
import logging
from .serializers import (
    ProductSerializer, ProductDetailSerializer, ProductCreateSerializer,
    ProductVariantSerializer, ProductImageSerializer, CategoryListSerializer, CategoryTreeSerializer,
    CategoryCreateSerializer
)
from django.db.models import Sum, Count


class TopSellingProductsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Get the top 3 best-selling products based on order quantities
        """
        shop_id = request.query_params.get('shop_id')

        # Changed 'product_variant__product' to 'variant__product'
        query = OrderItem.objects.values('variant__product')

        if shop_id:
            # Changed product_variant to variant
            query = query.filter(variant__product__shop_id=shop_id)

        top_selling_products = query.annotate(
            total_sold=Sum('quantity')
        ).order_by('-total_sold')[:3]

        result = []
        for item in top_selling_products:
            # Changed 'product_variant__product' to 'variant__product'
            product_id = item['variant__product']
            try:
                product = Product.objects.get(id=product_id)
                product_data = {
                    'id': product.id,
                    'name': product.name,
                    'total_sold': item['total_sold'],
                    # Add more product details as needed
                }
                result.append(product_data)
            except Product.DoesNotExist:
                continue

        return Response(result, status=status.HTTP_200_OK)


class FeaturedProductsView(APIView):
    """
    API để lấy các sản phẩm nổi bật ngẫu nhiên dựa trên đánh giá và số lượt mua
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        # Lấy tham số từ request
        limit = request.query_params.get('limit', 10)
        try:
            limit = int(limit)
            if limit <= 0:
                limit = 10
        except ValueError:
            limit = 10

        # Lấy các sản phẩm có trạng thái active và featured=True
        products = Product.objects.filter(
            status='active'
        ).order_by('-rating', '-sold_count')

        # Lấy 3 lần số lượng yêu cầu để có thể chọn ngẫu nhiên sau này
        products_pool = list(products[:limit * 3])

        # Nếu không đủ sản phẩm, lấy hết những sản phẩm có sẵn
        if len(products_pool) <= limit:
            selected_products = products_pool
        else:
            # Chọn ngẫu nhiên các sản phẩm từ pool
            selected_products = random.sample(products_pool, limit)

        serializer = ProductSerializer(selected_products, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ShopProductsView(APIView):
    """API để quản lý sản phẩm cho chủ cửa hàng"""
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)

    def get(self, request, shop_id):
        """Lấy danh sách sản phẩm thuộc cửa hàng kèm tổng số đã bán"""
        shop = get_object_or_404(Shop, id=shop_id)

        # Bắt đầu với tất cả sản phẩm của cửa hàng
        products = Product.objects.filter(shop=shop)

        # Annotate với số lượng đã bán
        products = products.annotate(
            total_sold=Sum(
                'variants__order_items__quantity',  # Changed from 'orderitem' to 'order_items'
                filter=Q(variants__order_items__status='completed'),  # Also changed here
                default=0
            )
        )

        # Lọc theo status, category, tìm kiếm tên
        product_status = request.query_params.get('status')
        category_id = request.query_params.get('category_id')
        search_query = request.query_params.get('search')
        sort_by = request.query_params.get('sort_by', 'created_at')
        sort_order = request.query_params.get('sort_order', 'desc')

        if product_status:
            products = products.filter(status=product_status)

        if category_id:
            products = products.filter(category_id=category_id)

        if search_query:
            products = products.filter(name__icontains=search_query)

        # Sắp xếp
        order_prefix = '-' if sort_order.lower() == 'desc' else ''
        if sort_by in ['name', 'price', 'stock', 'created_at', 'updated_at', 'sold_count', 'view_count']:
            products = products.order_by(f"{order_prefix}{sort_by}")

        # Phân trang
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 10))
        total_count = products.count()
        start = (page - 1) * page_size
        end = start + page_size
        paginated_products = products[start:end]

        # Serialize dữ liệu
        serializer = ProductSerializer(paginated_products, many=True)
        serialized_data = serializer.data

        # Thêm total_sold vào từng sản phẩm
        for i, product in enumerate(paginated_products):
            serialized_data[i]['total_sold'] = product.total_sold or 0

        return Response({
            'status': 'success',
            'message': 'Đã lấy danh sách sản phẩm thành công',
            'data': {
                'products': serialized_data,
                'pagination': {
                    'total': total_count,
                    'page': page,
                    'page_size': page_size,
                    'total_pages': (total_count + page_size - 1) // page_size
                }
            }
        }, status=status.HTTP_200_OK)

    @transaction.atomic
    def post(self, request, shop_id):
        """Tạo sản phẩm mới cho cửa hàng"""
        shop = get_object_or_404(Shop, id=shop_id)
        # logging.log(request.data)
        # Kiểm tra quyền sở hữu cửa hàng
        if shop.owner != request.user:
            return Response({
                'status': 'error',
                'message': 'Bạn không có quyền tạo sản phẩm cho cửa hàng này'
            }, status=status.HTTP_403_FORBIDDEN)

        # Thêm thông tin shop vào dữ liệu
        data = request.data.copy()
        data['shop'] = shop_id

        # Hoặc sử dụng timestamp (thời gian hiện tại)
        if 'slug' not in data or not data['slug']:
            timestamp = str(int(time.time()))
            data['slug'] = slugify(data.get('name', '')) + '-' + str(shop.id) + '-' + timestamp

        # Xử lý hình ảnh
        images_data = []
        if 'images' in request.FILES:
            images = request.FILES.getlist('images')
            for index, image_file in enumerate(images):
                upload_result = cloudinary.uploader.upload(
                    image_file,
                    folder=f"shops/{shop.id}/products",
                )
                image_url = upload_result.get('secure_url')
                images_data.append({
                    'image_url': image_url,
                    'is_thumbnail': index == 0,  # Đặt ảnh đầu tiên làm ảnh đại diện
                    'display_order': index
                })

        # Xử lý thuộc tính và biến thể
        attributes_data = data.pop('attributes', [])
        variants_data = data.pop('variants', [])

        # Serializer cho sản phẩm
        serializer = ProductCreateSerializer(data=data)

        if serializer.is_valid():
            # Lưu sản phẩm
            product = serializer.save()

            # Lưu hình ảnh sản phẩm
            for image_data in images_data:
                ProductImage.objects.create(product=product, **image_data)

            # Xử lý thuộc tính và biến thể
            self._process_attributes_and_variants(
                product, attributes_data, variants_data
            )

            # Lấy thông tin chi tiết sản phẩm đã tạo
            detail_serializer = ProductDetailSerializer(product)

            return Response({
                'status': 'success',
                'message': 'Đã tạo sản phẩm thành công',
                'data': detail_serializer.data
            }, status=status.HTTP_201_CREATED)

        return Response({
            'status': 'error',
            'message': 'Không thể tạo sản phẩm',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    def _process_attributes_and_variants(self, product, attributes_data, variants_data):
        """Xử lý thuộc tính và biến thể cho sản phẩm"""
        import json

        if isinstance(attributes_data, list) and len(attributes_data) == 1 and isinstance(attributes_data[0], str):
            attributes_data = attributes_data[0]

        # Parse attributes_data if it's a string (JSON)
        if isinstance(attributes_data, str):
            try:
                attributes_data = json.loads(attributes_data)
            except json.JSONDecodeError:
                attributes_data = []

        if isinstance(variants_data, list) and len(variants_data) == 1 and isinstance(variants_data[0], str):
            variants_data = variants_data[0]
        # Parse variants_data if it's a string (JSON)
        if isinstance(variants_data, str):
            try:
                variants_data = json.loads(variants_data)
            except json.JSONDecodeError:
                variants_data = []

        # Ensure we have lists
        if not isinstance(attributes_data, list):
            attributes_data = []
        if not isinstance(variants_data, list):
            variants_data = []

        # Xử lý thuộc tính
        attribute_map = {}  # Map attribute name -> attribute object
        attribute_value_map = {}  # Map (attribute_name, value) -> attribute_value object

        for attr_data in attributes_data:
            if not isinstance(attr_data, dict):
                continue

            attr_name = attr_data.get('name')
            attr_type = attr_data.get('type', 'other')
            attr_values = attr_data.get('values', [])

            # Tạo hoặc lấy thuộc tính
            attribute, _ = Attribute.objects.get_or_create(
                name=attr_name,
                defaults={
                    'display_name': attr_name.title() if attr_name else '',
                    'attribute_type': attr_type
                }
            )
            attribute_map[attr_name] = attribute

            # Tạo các giá trị thuộc tính
            for value_data in attr_values:
                if not isinstance(value_data, dict):
                    continue

                value = value_data.get('value')
                display = value_data.get('display', value)
                color_code = value_data.get('color_code') if attr_type == 'color' else None

                # Tạo hoặc lấy giá trị thuộc tính
                attr_value, _ = AttributeValue.objects.get_or_create(
                    attribute=attribute,
                    value=value,
                    defaults={
                        'display_value': display,
                        'color_code': color_code
                    }
                )
                attribute_value_map[(attr_name, value)] = attr_value

        # Xử lý biến thể
        for variant_data in variants_data:
            if not isinstance(variant_data, dict):
                continue

            sku = variant_data.get('sku', f"{product.slug}-{len(variants_data)}")
            price = variant_data.get('price', product.price)
            sale_price = variant_data.get('sale_price', product.sale_price)
            stock = variant_data.get('stock', 0)
            image_url = variant_data.get('image_url')

        # Tạo biến thể
            variant = ProductVariant.objects.create(
                product=product,
                sku=sku,
                price=price,
                sale_price=sale_price,
                stock=stock,
                image_url=image_url
            )

            logging.debug(f"Creating variant: SKU={sku}, price={price}, sale_price={sale_price}, stock={stock}")

            # Gắn các giá trị thuộc tính cho biến thể
            variant_attributes = variant_data.get('attributes', {})
            # Log for debugging
            logging.debug(f"Attributes cho biến thể {sku}: {variant_attributes}")

            # Handle both dictionary format and list format
            if isinstance(variant_attributes, dict):
                # Dictionary format (name: value)
                for attr_name, attr_value in variant_attributes.items():
                    if attr_name in attribute_map and (attr_name, attr_value) in attribute_value_map:
                        VariantAttributeValue.objects.create(
                            variant=variant,
                            attribute_value=attribute_value_map[(attr_name, attr_value)]
                        )
            elif isinstance(variant_attributes, list):
                # List format [{name: ..., value: ...}, ...]
                for attr_item in variant_attributes:
                    if isinstance(attr_item, dict):
                        attr_name = attr_item.get('name')
                        attr_value = attr_item.get('value')
                        if attr_name in attribute_map and (attr_name, attr_value) in attribute_value_map:
                            VariantAttributeValue.objects.create(
                                variant=variant,
                                attribute_value=attribute_value_map[(attr_name, attr_value)]
                            )


class ProductDetailView(APIView):
    # Cập nhật quyền truy cập - Cho phép tất cả người dùng truy cập
    permission_classes = [permissions.AllowAny]
    parser_classes = (MultiPartParser, FormParser)

    def get(self, request, product_id):
        """Lấy thông tin chi tiết của một sản phẩm"""
        product = get_object_or_404(Product, id=product_id)

        # Tăng số lượt xem
        product.view_count += 1
        product.save(update_fields=['view_count'])

        serializer = ProductDetailSerializer(product)

        return Response({
            'status': 'success',
            'message': 'Đã lấy thông tin chi tiết sản phẩm thành công',
            'data': serializer.data
        }, status=status.HTTP_200_OK)

    @transaction.atomic
    def put(self, request, product_id):
        """Cập nhật thông tin sản phẩm"""
        product = get_object_or_404(Product, id=product_id)

        # Kiểm tra quyền sở hữu cửa hàng
        if product.shop.owner != request.user:
            return Response({
                'status': 'error',
                'message': 'Bạn không có quyền cập nhật sản phẩm này'
            }, status=status.HTTP_403_FORBIDDEN)

        # Cập nhật thông tin cơ bản của sản phẩm
        serializer = ProductSerializer(product, data=request.data, partial=True)

        if serializer.is_valid():
            product = serializer.save()

            # Xử lý hình ảnh mới (nếu có)
            if 'images' in request.FILES:
                images = request.FILES.getlist('images')
                for index, image_file in enumerate(images):
                    upload_result = cloudinary.uploader.upload(
                        image_file,
                        folder=f"shops/{product.shop.id}/products",
                    )
                    image_url = upload_result.get('secure_url')

                    # Tạo hình ảnh mới
                    ProductImage.objects.create(
                        product=product,
                        image_url=image_url,
                        is_thumbnail=False,  # Không đặt là thumbnail mặc định
                        display_order=ProductImage.objects.filter(product=product).count() + index
                    )

            # Cập nhật biến thể (nếu có)
            if 'variants' in request.data:
                self._update_variants(product, request.data.get('variants', []))

            # Lấy thông tin chi tiết sản phẩm đã cập nhật
            updated_serializer = ProductDetailSerializer(product)

            return Response({
                'status': 'success',
                'message': 'Đã cập nhật sản phẩm thành công',
                'data': updated_serializer.data
            }, status=status.HTTP_200_OK)

        return Response({
            'status': 'error',
            'message': 'Không thể cập nhật sản phẩm',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, product_id):
        """Xóa sản phẩm"""
        product = get_object_or_404(Product, id=product_id)

        # Kiểm tra quyền sở hữu cửa hàng
        if product.shop.owner != request.user:
            return Response({
                'status': 'error',
                'message': 'Bạn không có quyền xóa sản phẩm này'
            }, status=status.HTTP_403_FORBIDDEN)

        # Kiểm tra xem sản phẩm đã được đặt hàng chưa
        # (Bạn có thể thêm logic kiểm tra đơn hàng ở đây)

        # Lưu tên sản phẩm để trả về trong phản hồi
        product_name = product.name

        # Xóa sản phẩm và tất cả dữ liệu liên quan (variants, images, etc.)
        product.delete()

        return Response({
            'status': 'success',
            'message': f'Sản phẩm "{product_name}" đã được xóa thành công'
        }, status=status.HTTP_200_OK)

    def _update_variants(self, product, variants_data):
        """Cập nhật các biến thể của sản phẩm"""
        # Check if variants_data is a string (JSON) and parse it
        if isinstance(variants_data, str):
            try:
                import json
                variants_data = json.loads(variants_data)
            except json.JSONDecodeError:
                # Handle invalid JSON
                return

        # Xóa tất cả biến thể hiện có của sản phẩm
        # ProductVariant.objects.filter(product=product).delete()

        # Thêm các biến thể mới
        for variant_data in variants_data:
            # Make sure variant_data is a dictionary
            if not isinstance(variant_data, dict):
                continue

            # Tạo biến thể mới
            sku = variant_data.get('sku', f"{product.slug}-{ProductVariant.objects.filter(product=product).count() + 1}")
            price = variant_data.get('price', product.price)
            sale_price = variant_data.get('sale_price', product.sale_price)
            stock = variant_data.get('stock', 0)
            image_url = variant_data.get('image_url')

            # Tạo biến thể mới
            variant = ProductVariant.objects.create(
                product=product,
                sku=sku,
                price=price,
                sale_price=sale_price,
                stock=stock,
                image_url=image_url
            )

            # Xử lý các giá trị thuộc tính của biến thể
            if 'attribute_values' in variant_data:
                for attr_value_id in variant_data.get('attribute_values', []):
                    try:
                        attr_value = AttributeValue.objects.get(id=attr_value_id)
                        VariantAttributeValue.objects.create(
                            variant=variant,
                            attribute_value=attr_value
                        )
                    except AttributeValue.DoesNotExist:
                        # Bỏ qua nếu giá trị thuộc tính không tồn tại
                        pass


class ProductImageManagementView(APIView):
    """API để quản lý hình ảnh của sản phẩm"""
    permission_classes = [IsShopOwner]
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, product_id):
        """Thêm hình ảnh mới cho sản phẩm"""
        product = get_object_or_404(Product, id=product_id)

        # Kiểm tra quyền sở hữu cửa hàng
        if product.shop.owner != request.user:
            return Response({
                'status': 'error',
                'message': 'Bạn không có quyền thêm hình ảnh cho sản phẩm này'
            }, status=status.HTTP_403_FORBIDDEN)

        if 'image' not in request.FILES:
            return Response({
                'status': 'error',
                'message': 'Không có hình ảnh được cung cấp'
            }, status=status.HTTP_400_BAD_REQUEST)

        image_file = request.FILES['image']
        is_thumbnail = request.data.get('is_thumbnail', False)

        # Tải lên hình ảnh vào Cloudinary
        upload_result = cloudinary.uploader.upload(
            image_file,
            folder=f"shops/{product.shop.id}/products",
        )
        image_url = upload_result.get('secure_url')

        # Nếu đặt làm ảnh đại diện, cập nhật các ảnh khác
        if is_thumbnail:
            ProductImage.objects.filter(product=product, is_thumbnail=True).update(is_thumbnail=False)

        # Tạo bản ghi hình ảnh mới
        image = ProductImage.objects.create(
            product=product,
            image_url=image_url,
            is_thumbnail=is_thumbnail,
            display_order=ProductImage.objects.filter(product=product).count()
        )

        serializer = ProductImageSerializer(image)

        return Response({
            'status': 'success',
            'message': 'Đã thêm hình ảnh sản phẩm thành công',
            'data': serializer.data
        }, status=status.HTTP_201_CREATED)

    def delete(self, request, product_id, image_id):
        """Xóa hình ảnh sản phẩm"""
        product = get_object_or_404(Product, id=product_id)

        # Kiểm tra quyền sở hữu cửa hàng
        if product.shop.owner != request.user:
            return Response({
                'status': 'error',
                'message': 'Bạn không có quyền xóa hình ảnh của sản phẩm này'
            }, status=status.HTTP_403_FORBIDDEN)

        image = get_object_or_404(ProductImage, id=image_id, product=product)

        # Kiểm tra nếu là hình ảnh đại diện và có nhiều hơn một hình ảnh
        if image.is_thumbnail and ProductImage.objects.filter(product=product).count() > 1:
            # Đặt hình ảnh khác làm ảnh đại diện
            new_thumbnail = ProductImage.objects.filter(product=product).exclude(id=image_id).first()
            if new_thumbnail:
                new_thumbnail.is_thumbnail = True
                new_thumbnail.save()

        # Xóa hình ảnh
        image.delete()

        return Response({
            'status': 'success',
            'message': 'Đã xóa hình ảnh sản phẩm thành công'
        }, status=status.HTTP_200_OK)

    def put(self, request, product_id, image_id):
        """Cập nhật thông tin hình ảnh (đặt làm ảnh đại diện, thay đổi thứ tự hiển thị)"""
        product = get_object_or_404(Product, id=product_id)

        # Kiểm tra quyền sở hữu cửa hàng
        if product.shop.owner != request.user:
            return Response({
                'status': 'error',
                'message': 'Bạn không có quyền cập nhật hình ảnh của sản phẩm này'
            }, status=status.HTTP_403_FORBIDDEN)

        image = get_object_or_404(ProductImage, id=image_id, product=product)

        # Cập nhật thông tin
        if 'is_thumbnail' in request.data and request.data['is_thumbnail']:
            # Nếu đặt làm ảnh đại diện, cập nhật các ảnh khác
            ProductImage.objects.filter(product=product, is_thumbnail=True).update(is_thumbnail=False)
            image.is_thumbnail = True

        if 'display_order' in request.data:
            image.display_order = request.data['display_order']

        image.save()

        serializer = ProductImageSerializer(image)

        return Response({
            'status': 'success',
            'message': 'Đã cập nhật thông tin hình ảnh sản phẩm',
            'data': serializer.data
        }, status=status.HTTP_200_OK)


class ProductVariantManagementView(APIView):
    """API để quản lý biến thể sản phẩm"""
    permission_classes = [IsShopOwner]

    def post(self, request, product_id):
        """Thêm biến thể mới cho sản phẩm"""
        product = get_object_or_404(Product, id=product_id)

        # Kiểm tra quyền sở hữu cửa hàng
        if product.shop.owner != request.user:
            return Response({
                'status': 'error',
                'message': 'Bạn không có quyền thêm biến thể cho sản phẩm này'
            }, status=status.HTTP_403_FORBIDDEN)

        # Thêm ID sản phẩm vào dữ liệu
        data = request.data.copy()
        data['product'] = product_id

        # Tạo SKU tự động nếu không được cung cấp
        if 'sku' not in data or not data['sku']:
            data['sku'] = f"{product.slug}-{ProductVariant.objects.filter(product=product).count() + 1}"

        # Serializer cho biến thể
        serializer = ProductVariantSerializer(data=data)

        if serializer.is_valid():
            variant = serializer.save()

            # Xử lý các giá trị thuộc tính của biến thể
            if 'attribute_values' in data:
                for attr_value_id in data.get('attribute_values', []):
                    try:
                        attr_value = AttributeValue.objects.get(id=attr_value_id)
                        VariantAttributeValue.objects.create(
                            variant=variant,
                            attribute_value=attr_value
                        )
                    except AttributeValue.DoesNotExist:
                        # Bỏ qua nếu giá trị thuộc tính không tồn tại
                        pass

            return Response({
                'status': 'success',
                'message': 'Đã thêm biến thể sản phẩm thành công',
                'data': serializer.data
            }, status=status.HTTP_201_CREATED)

        return Response({
            'status': 'error',
            'message': 'Không thể thêm biến thể sản phẩm',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, product_id, variant_id):
        """Cập nhật biến thể sản phẩm"""
        product = get_object_or_404(Product, id=product_id)

        # Kiểm tra quyền sở hữu cửa hàng
        if product.shop.owner != request.user:
            return Response({
                'status': 'error',
                'message': 'Bạn không có quyền cập nhật biến thể của sản phẩm này'
            }, status=status.HTTP_403_FORBIDDEN)

        # Lấy biến thể cần cập nhật
        variant = get_object_or_404(ProductVariant, id=variant_id, product=product)

        # Cập nhật thông tin biến thể
        serializer = ProductVariantSerializer(variant, data=request.data, partial=True)

        if serializer.is_valid():
            variant = serializer.save()

            # Cập nhật các giá trị thuộc tính của biến thể
            if 'attribute_values' in request.data:
                # Xóa các giá trị thuộc tính hiện tại
                VariantAttributeValue.objects.filter(variant=variant).delete()

                # Thêm các giá trị thuộc tính mới
                for attr_value_id in request.data.get('attribute_values', []):
                    try:
                        attr_value = AttributeValue.objects.get(id=attr_value_id)
                        VariantAttributeValue.objects.create(
                            variant=variant,
                            attribute_value=attr_value
                        )
                    except AttributeValue.DoesNotExist:
                        # Bỏ qua nếu giá trị thuộc tính không tồn tại
                        pass

            return Response({
                'status': 'success',
                'message': 'Đã cập nhật biến thể sản phẩm thành công',
                'data': serializer.data
            }, status=status.HTTP_200_OK)

        return Response({
            'status': 'error',
            'message': 'Không thể cập nhật biến thể sản phẩm',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, product_id, variant_id):
        """Xóa biến thể sản phẩm"""
        product = get_object_or_404(Product, id=product_id)

        # Kiểm tra quyền sở hữu cửa hàng
        if product.shop.owner != request.user:
            return Response({
                'status': 'error',
                'message': 'Bạn không có quyền xóa biến thể của sản phẩm này'
            }, status=status.HTTP_403_FORBIDDEN)

        # Lấy biến thể cần xóa
        variant = get_object_or_404(ProductVariant, id=variant_id, product=product)

        # Kiểm tra xem sản phẩm có nhiều hơn một biến thể không
        if ProductVariant.objects.filter(product=product).count() <= 1:
            return Response({
                'status': 'error',
                'message': 'Không thể xóa biến thể duy nhất của sản phẩm'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Xóa biến thể
        variant.delete()

        return Response({
            'status': 'success',
            'message': 'Đã xóa biến thể sản phẩm thành công'
        }, status=status.HTTP_200_OK)

# Add these helper methods to your views module

class ShopProductStatsView(APIView):
    """API để lấy thống kê sản phẩm của cửa hàng"""
    permission_classes = [IsShopOwner]

    def get(self, request, shop_id):
        """Lấy thống kê sản phẩm của cửa hàng"""
        shop = get_object_or_404(Shop, id=shop_id)

        # Kiểm tra quyền sở hữu cửa hàng
        if shop.owner != request.user:
            return Response({
                'status': 'error',
                'message': 'Bạn không có quyền xem thống kê cửa hàng này'
            }, status=status.HTTP_403_FORBIDDEN)

        # Tính toán các thống kê
        total_products = Product.objects.filter(shop=shop).count()
        active_products = Product.objects.filter(shop=shop, status='active').count()
        out_of_stock_products = Product.objects.filter(shop=shop, status='out_of_stock').count()
        inactive_products = Product.objects.filter(shop=shop, status='inactive').count()

        # Thống kê theo danh mục
        category_stats = []
        categories = Category.objects.filter(products__shop=shop).distinct()
        for category in categories:
            category_stats.append({
                'id': category.id,
                'name': category.name,
                'count': Product.objects.filter(shop=shop, category=category).count()
            })

        # Tính tổng số lượng hàng tồn kho
        total_stock = Product.objects.filter(shop=shop).aggregate(total=models.Sum('stock'))['total'] or 0

        # Tính tổng doanh số (nếu có dữ liệu đơn hàng)
        # (Ở đây bạn có thể tích hợp với mô hình đơn hàng của bạn)

        return Response({
            'status': 'success',
            'message': 'Đã lấy thống kê sản phẩm của cửa hàng',
            'data': {
                'total_products': total_products,
                'active_products': active_products,
                'out_of_stock_products': out_of_stock_products,
                'inactive_products': inactive_products,
                'total_stock': total_stock,
                'category_stats': category_stats
            }
        }, status=status.HTTP_200_OK)


class ProductBulkActionView(APIView):
    """API để thực hiện hành động hàng loạt trên sản phẩm"""
    permission_classes = [IsShopOwner]

    def post(self, request, shop_id):
        """Thực hiện hành động hàng loạt trên sản phẩm"""
        shop = get_object_or_404(Shop, id=shop_id)

        # Kiểm tra quyền sở hữu cửa hàng
        if shop.owner != request.user:
            return Response({
                'status': 'error',
                'message': 'Bạn không có quyền thực hiện hành động này'
            }, status=status.HTTP_403_FORBIDDEN)

        action = request.data.get('action')
        product_ids = request.data.get('product_ids', [])

        if not product_ids:
            return Response({
                'status': 'error',
                'message': 'Không có sản phẩm nào được chọn'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Lấy các sản phẩm thuộc cửa hàng
        products = Product.objects.filter(shop=shop, id__in=product_ids)

        if not products.exists():
            return Response({
                'status': 'error',
                'message': 'Không tìm thấy sản phẩm nào khớp với yêu cầu'
            }, status=status.HTTP_404_NOT_FOUND)

        if action == 'activate':
            # Kích hoạt sản phẩm
            products.update(status='active')
            message = f'Đã kích hoạt {products.count()} sản phẩm'
        elif action == 'deactivate':
            # Vô hiệu hóa sản phẩm
            products.update(status='inactive')
            message = f'Đã vô hiệu hóa {products.count()} sản phẩm'
        elif action == 'mark_out_of_stock':
            # Đánh dấu hết hàng
            products.update(status='out_of_stock')
            message = f'Đã đánh dấu {products.count()} sản phẩm là hết hàng'
        elif action == 'set_featured':
            # Đặt làm sản phẩm nổi bật
            products.update(featured=True)
            message = f'Đã đặt {products.count()} sản phẩm làm nổi bật'
        elif action == 'unset_featured':
            # Bỏ đặt làm sản phẩm nổi bật
            products.update(featured=False)
            message = f'Đã bỏ đặt {products.count()} sản phẩm làm nổi bật'
        elif action == 'delete':
            # Xóa sản phẩm
            count = products.count()
            products.delete()
            message = f'Đã xóa {count} sản phẩm'
        else:
            return Response({
                'status': 'error',
                'message': 'Hành động không hợp lệ'
            }, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            'status': 'success',
            'message': message
        }, status=status.HTTP_200_OK)


# products/views.py - thêm vào file views.py hiện có

class CategoryListView(APIView):
    """API để lấy danh sách tất cả danh mục sản phẩm"""
    permission_classes = [permissions.AllowAny]
    def get(self, request):
        """Lấy danh sách tất cả danh mục"""
        # Lấy tham số truy vấn
        format_type = request.query_params.get('format', 'flat')
        status_filter = request.query_params.get('status', 'active')

        # Lọc danh mục theo trạng thái nếu được chỉ định
        if status_filter and status_filter != 'all':
            categories = Category.objects.filter(status=status_filter)
        else:
            categories = Category.objects.all()

        # Trả về danh sách phẳng hoặc cấu trúc cây tùy thuộc vào tham số format
        if format_type == 'tree':
            # Chỉ lấy danh mục gốc (không có danh mục cha)
            root_categories = categories.filter(parent=None)
            serializer = CategoryTreeSerializer(root_categories, many=True)
        else:
            serializer = CategoryListSerializer(categories, many=True)

        return Response({
            'status': 'success',
            'message': 'Đã lấy danh sách danh mục thành công',
            'data': serializer.data
        }, status=status.HTTP_200_OK)


class CategoryDetailView(APIView):
    """API để quản lý một danh mục cụ thể"""
    permission_classes = [IsAdminUser]

    def get(self, request, category_id):
        """Lấy thông tin chi tiết của một danh mục"""
        category = get_object_or_404(Category, id=category_id)

        # Xác định xem có muốn hiển thị cả cấu trúc cây con không
        include_children = request.query_params.get('include_children', 'false').lower() == 'true'

        if include_children:
            serializer = CategoryTreeSerializer(category)
        else:
            serializer = CategoryListSerializer(category)

        # Lấy tổng số sản phẩm trong danh mục này
        product_count = Product.objects.filter(category=category).count()

        # Lấy danh mục cha (nếu có)
        parent = None
        if category.parent:
            parent = {
                'id': category.parent.id,
                'name': category.parent.name
            }

        return Response({
            'status': 'success',
            'message': 'Đã lấy thông tin danh mục thành công',
            'data': {
                **serializer.data,
                'product_count': product_count,
                'parent': parent
            }
        }, status=status.HTTP_200_OK)

    def post(self, request):
        """Tạo danh mục mới (chỉ dành cho quản trị viên)"""
        serializer = CategoryCreateSerializer(data=request.data)

        if serializer.is_valid():
            # Get parent category if specified
            parent_id = request.data.get('parent')
            if parent_id:
                try:
                    parent = Category.objects.get(id=parent_id)
                    serializer.validated_data['parent'] = parent
                except Category.DoesNotExist:
                    return Response({
                        'status': 'error',
                        'message': 'Danh mục cha không tồn tại',
                    }, status=status.HTTP_400_BAD_REQUEST)

            # Save the new category
            category = serializer.save()

            return Response({
                'status': 'success',
                'message': 'Đã tạo danh mục mới thành công',
                'data': CategoryListSerializer(category).data
            }, status=status.HTTP_201_CREATED)

        return Response({
            'status': 'error',
            'message': 'Dữ liệu không hợp lệ',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.db.models import Q, Count, Avg
from products.models import Product, Category


class CategoryProductsView(APIView):
    """API to get products by category with filters, search, and sorting"""
    permission_classes = [permissions.AllowAny]

    def get(self, request, category_id=None):
        try:
            # Nếu không có category_id trong URL thì lấy từ query params
            if not category_id:
                category_id = request.query_params.get('category_id')

            category_info = None
            category_ids = []

            if category_id:
                try:
                    category = Category.objects.get(id=category_id)
                    category_info = {
                        'id': category.id,
                        'name': category.name,
                        'description': category.description,
                        'image': category.image,
                        'parent_id': category.parent.id if category.parent else None
                    }
                    category_ids = [category.id]
                    child_ids = Category.objects.filter(parent=category).values_list('id', flat=True)
                    category_ids.extend(child_ids)
                except Category.DoesNotExist:
                    return Response({
                        'status': 'error',
                        'message': 'Danh mục không tồn tại'
                    }, status=status.HTTP_404_NOT_FOUND)

            # Lọc theo danh mục (nếu có)
            products = Product.objects.filter(status='active')
            if category_ids:
                products = products.filter(category_id__in=category_ids)

            # Lọc tìm kiếm theo tên, mô tả
            search = request.query_params.get('q')
            if search:
                products = products.filter(
                    Q(name__icontains=search)
                )

            # Lọc theo giá
            min_price = request.query_params.get('min_price')
            max_price = request.query_params.get('max_price')

            if min_price:
                try:
                    products = products.filter(price__gte=float(min_price))
                except ValueError:
                    pass

            if max_price:
                try:
                    products = products.filter(price__lte=float(max_price))
                except ValueError:
                    pass

            # Lọc theo shop hoặc brand
            shop_id = request.query_params.get('shop_id')
            brand_id = request.query_params.get('brand_id')

            if shop_id:
                products = products.filter(shop_id=shop_id)
            if brand_id:
                products = products.filter(brand_id=brand_id)

            # Annotate dữ liệu cần thiết
            products = products.annotate(
                avg_rating=Avg('reviews__rating'),
                total_sold=Count('order_items', filter=Q(order_items__status__in=[
                    'delivered', 'received', 'received_reviewed'
                ]))
            )

            # Sắp xếp
            sort_by = request.query_params.get('sort_by', 'latest')
            sort_map = {
                'price_asc': 'price',
                'price_desc': '-price',
                'name_asc': 'name',
                'name_desc': '-name',
                'rating': '-avg_rating',
                'popular': '-total_sold',
                'latest': '-created_at'
            }
            sort_field = sort_map.get(sort_by, '-created_at')
            products = products.order_by(sort_field)

            # Phân trang
            page = int(request.query_params.get('page', 1))
            page_size = int(request.query_params.get('page_size', 20))
            paginator = Paginator(products, page_size)
            total_count = paginator.count

            try:
                paginated_products = paginator.page(page)
            except (PageNotAnInteger, EmptyPage):
                paginated_products = paginator.page(1)

            serializer = ProductSerializer(paginated_products, many=True, context={'request': request})

            return Response({
                'status': 'success',
                'message': 'Lấy danh sách sản phẩm thành công',
                'data': {
                    'category': category_info,
                    'products': serializer.data,
                    'pagination': {
                        'total': total_count,
                        'page': page,
                        'page_size': page_size,
                        'total_pages': paginator.num_pages
                    },
                    'filters': {
                        'min_price': min_price,
                        'max_price': max_price,
                        'shop_id': shop_id,
                        'brand_id': brand_id,
                        'search': search,
                        'sort_by': sort_by
                    }
                }
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)