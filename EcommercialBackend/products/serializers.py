from rest_framework import serializers
from shops.serializers import ShopListSerializer
from .models import (
    Product, ProductImage, ProductVariant,
    Attribute, AttributeValue, VariantAttributeValue,
    Tag, ProductTag, Category, Brand
)


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'image', 'status']


class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = ['id', 'name', 'logo', 'status']


class AttributeValueSerializer(serializers.ModelSerializer):
    attribute = serializers.SerializerMethodField()
    value = serializers.SerializerMethodField()

    class Meta:
        model = AttributeValue
        fields = ['id', 'value', 'display_value', 'attribute']

    def get_attribute(self, obj):
        attribute_obj = obj.attribute_value.attribute
        return {
            'id': attribute_obj.id,
            'name': attribute_obj.name,
            'display_name': attribute_obj.display_name,
            'attribute_type': attribute_obj.attribute_type
        }

    def get_value(self, obj):
        return obj.attribute_value.value

class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['id', 'image_url', 'is_thumbnail', 'display_order', 'created_at']


class ProductVariantSerializer(serializers.ModelSerializer):
    attribute_values = AttributeValueSerializer(read_only=True, many=True, source='attribute_values.all')

    class Meta:
        model = ProductVariant
        fields = ['id', 'product', 'sku', 'price', 'sale_price',
                  'stock', 'image_url', 'attribute_values', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.ReadOnlyField(source='category.name')
    shop_name = serializers.ReadOnlyField(source='shop.name')
    thumbnail = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ['id', 'shop', 'shop_name', 'category', 'category_name',
                  'name', 'slug','description', 'short_description', 'price', 'sale_price',
                  'stock', 'product_type', 'status', 'featured',
                  'rating', 'view_count', 'sold_count', 'thumbnail',
                  'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_thumbnail(self, obj):
        """Lấy URL hình ảnh đại diện của sản phẩm"""
        thumbnail = obj.images.filter(is_thumbnail=True).first()
        if thumbnail:
            return thumbnail.image_url
        return None


class ProductCreateSerializer(serializers.ModelSerializer):
    """Serializer for product creation"""

    class Meta:
        model = Product
        fields = ['id', 'shop', 'category', 'name', 'slug', 'description',
                  'short_description', 'price', 'sale_price', 'stock',
                  'product_type', 'status', 'featured']
        read_only_fields = ['id']

    def validate(self, data):
        """Xác thực dữ liệu"""
        # Kiểm tra giá khuyến mãi không lớn hơn giá gốc
        if 'sale_price' in data and data['sale_price'] and data['sale_price'] > data['price']:
            raise serializers.ValidationError(
                {"sale_price": "Giá khuyến mãi phải nhỏ hơn giá gốc"}
            )
        return data


class ProductDetailSerializer(serializers.ModelSerializer):
    """Serializer for detailed product information"""
    shop = ShopListSerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)
    variants = ProductVariantSerializer(many=True, read_only=True)
    tags = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ['id', 'shop', 'category', 'name', 'slug',
                  'description', 'short_description', 'price', 'sale_price',
                  'stock', 'product_type', 'status', 'featured',
                  'rating', 'view_count', 'sold_count', 'images',
                  'variants', 'tags', 'created_at', 'updated_at']

    def get_tags(self, obj):
        """Lấy danh sách tag của sản phẩm"""
        tags = obj.tags.all()
        return [{'id': tag.tag.id, 'name': tag.tag.name} for tag in tags]


class AttributeSerializer(serializers.ModelSerializer):
    values = AttributeValueSerializer(many=True, read_only=True)

    class Meta:
        model = Attribute
        fields = ['id', 'name', 'display_name', 'attribute_type', 'values']


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name']


# products/serializers.py - thêm vào file serializers.py hiện có

class CategoryListSerializer(serializers.ModelSerializer):
    """Serializer đơn giản để hiển thị danh sách danh mục"""

    class Meta:
        model = Category
        fields = ['id', 'name', 'image', 'status', 'parent']


class RecursiveCategorySerializer(serializers.Serializer):
    """Serializer đệ quy để hiển thị cấu trúc danh mục dạng cây"""

    def to_representation(self, instance):
        serializer = CategoryTreeSerializer(instance, context=self.context)
        return serializer.data


class CategoryTreeSerializer(serializers.ModelSerializer):
    """Serializer để hiển thị cấu trúc danh mục dạng cây"""
    children = RecursiveCategorySerializer(many=True, read_only=True)
    product_count = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['id', 'name', 'image', 'description', 'status', 'product_count', 'children']

    def get_product_count(self, obj):
        """Lấy số lượng sản phẩm của danh mục"""
        return obj.products.count()


class CategoryCreateSerializer(serializers.ModelSerializer):
    """Serializer để tạo danh mục mới"""

    class Meta:
        model = Category
        fields = ['name', 'description', 'image', 'status']