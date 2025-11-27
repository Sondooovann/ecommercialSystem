# cart/serializers.py
from rest_framework import serializers
from .models import Cart, CartItem
from products.models import ProductVariant, Product
from products.serializers import ProductVariantSerializer


class CartItemSerializer(serializers.ModelSerializer):
    variant_details = serializers.SerializerMethodField()
    price = serializers.SerializerMethodField()
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = ['id', 'variant', 'variant_details', 'quantity', 'price', 'total_price', 'created_at']
        read_only_fields = ['id', 'created_at']

    def get_variant_details(self, obj):
        """Lấy thông tin chi tiết về biến thể sản phẩm"""
        product = obj.variant.product
        return {
            'id': obj.variant.id,
            'product_id': product.id,
            'product_slug': product.slug,  # Thêm slug của sản phẩm
            'product_name': product.name,
            'sku': obj.variant.sku,
            'image_url': obj.variant.image_url or self._get_product_image(product),
            'attributes': self._get_attributes(obj.variant),
            'stock': obj.variant.stock,
            'shop_id': product.shop.id,  # Thêm ID của cửa hàng
            'shop_name': product.shop.name  # Thêm tên cửa hàng
        }

    # Phần còn lại giữ nguyên
    def _get_product_image(self, product):
        """Lấy hình ảnh đại diện của sản phẩm"""
        thumbnail = product.images.filter(is_thumbnail=True).first()
        if thumbnail:
            return thumbnail.image_url
        # Lấy hình ảnh đầu tiên nếu không có thumbnail
        first_image = product.images.first()
        if first_image:
            return first_image.image_url
        return None

    def _get_attributes(self, variant):
        """Lấy các thuộc tính của biến thể"""
        attributes = []
        attribute_values = variant.attribute_values.all().select_related('attribute_value__attribute')

        for attr_value in attribute_values:
            attribute = attr_value.attribute_value.attribute
            attributes.append({
                'name': attribute.name,
                'display_name': attribute.display_name,
                'value': attr_value.attribute_value.value,
                'display_value': attr_value.attribute_value.display_value
            })

        return attributes

    def get_price(self, obj):
        """Lấy giá của biến thể sản phẩm"""
        variant = obj.variant
        # Sử dụng giá khuyến mãi nếu có
        if variant.sale_price:
            return variant.sale_price
        # Sử dụng giá biến thể nếu có
        if variant.price:
            return variant.price
        # Sử dụng giá sản phẩm nếu không có giá biến thể
        product = variant.product
        if product.sale_price:
            return product.sale_price
        return product.price

    def get_total_price(self, obj):
        """Tính tổng giá tiền cho item này"""
        return self.get_price(obj) * obj.quantity


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total_items = serializers.SerializerMethodField()
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = ['id', 'user', 'items', 'total_items', 'total_price', 'created_at', 'updated_at']
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']

    def get_total_items(self, obj):
        """Lấy tổng số lượng sản phẩm trong giỏ hàng"""
        return sum(item.quantity for item in obj.items.all())

    def get_total_price(self, obj):
        """Tính tổng giá trị giỏ hàng"""
        total = 0
        cart_items = obj.items.all()
        for item in cart_items:
            # Lấy giá
            variant = item.variant
            price = 0
            # Sử dụng giá khuyến mãi nếu có
            if variant.sale_price:
                price = variant.sale_price
            # Sử dụng giá biến thể nếu có
            elif variant.price:
                price = variant.price
            # Sử dụng giá sản phẩm nếu không có giá biến thể
            else:
                product = variant.product
                if product.sale_price:
                    price = product.sale_price
                else:
                    price = product.price

            total += price * item.quantity

        return total


class AddToCartSerializer(serializers.Serializer):
    variant_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1, default=1)

    def validate_variant_id(self, value):
        """Kiểm tra biến thể tồn tại và có sẵn"""
        try:
            variant = ProductVariant.objects.get(pk=value)
            if variant.stock <= 0:
                raise serializers.ValidationError("Sản phẩm này đã hết hàng")
            return value
        except ProductVariant.DoesNotExist:
            raise serializers.ValidationError("Biến thể sản phẩm không tồn tại")


class UpdateCartItemSerializer(serializers.Serializer):
    quantity = serializers.IntegerField(min_value=1)
