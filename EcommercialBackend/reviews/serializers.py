# reviews/serializers.py
from rest_framework import serializers
from .models import Review, ReviewLike, OrderReview
from products.models import Product
from orders.models import OrderItem, Order
import json

from .utils import check_forbidden_words


# reviews/serializers.py
class OrderReviewDetailSerializer(serializers.ModelSerializer):
    user_info = serializers.SerializerMethodField()
    product_info = serializers.SerializerMethodField()
    images = serializers.SerializerMethodField()

    class Meta:
        model = OrderReview
        fields = ['id', 'order_id', 'rating', 'comment', 'images',
                  'created_at', 'status', 'user_info', 'product_info']

    def get_user_info(self, obj):
        user = obj.user
        return {
            'id': user.id,
            'full_name': user.full_name,
            'avatar': user.avatar.url if hasattr(user, 'avatar') and user.avatar else None
        }

    def get_product_info(self, obj):
        # Lấy product_id từ context
        product_id = self.context.get('product_id')
        if not product_id:
            return None

        # Tìm sản phẩm trong đơn hàng
        item = obj.order.items.filter(product_id=product_id).first()
        if not item:
            return None

        product = item.product
        return {
            'id': product.id,
            'name': product.name,
            'thumbnail': product.images.filter(is_thumbnail=True).first().image_url if product.images.filter(is_thumbnail=True).exists() else None
        }

    def get_images(self, obj):
        if not obj.images:
            return []

        try:
            # Nếu images lưu dưới dạng JSON string
            return json.loads(obj.images)
        except:
            # Nếu images đã là list
            return obj.images if isinstance(obj.images, list) else []

class ReviewSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()
    product_name = serializers.SerializerMethodField()
    like_count = serializers.SerializerMethodField()

    class Meta:
        model = Review
        fields = ['id', 'product', 'user', 'order_item', 'rating', 'comment',
                  'images', 'status', 'created_at', 'user_name', 'product_name', 'like_count']
        read_only_fields = ['user', 'status', 'created_at']

    def get_user_name(self, obj):
        return obj.user.full_name or obj.user.email

    def get_product_name(self, obj):
        return obj.product.name

    def get_like_count(self, obj):
        return obj.likes.count()

    def validate_order_item(self, value):
        # Kiểm tra xem người dùng hiện tại có sở hữu order_item này không
        request = self.context.get('request')
        if request and request.user:
            if value.order.user != request.user:
                raise serializers.ValidationError("You can only review products from your own orders.")

            # Kiểm tra order đã được giao hàng chưa
            if value.order.order_status != 'received':  # Changed from status to order_status
                raise serializers.ValidationError("You can only review products from received orders.")

            # Kiểm tra đã đánh giá order_item này chưa
            if Review.objects.filter(user=request.user, order_item=value).exists():
                raise serializers.ValidationError("You have already reviewed this order item.")

        return value

    def validate_rating(self, value):
        if not 1 <= value <= 5:
            raise serializers.ValidationError("Rating must be between 1 and 5.")
        return value

    def create(self, validated_data):
        # Tự động thêm user và product từ order_item
        validated_data['user'] = self.context['request'].user
        validated_data['product'] = validated_data['order_item'].variant.product
        return super().create(validated_data)

    def validate_comment(self, value):
        if value:
            contains_forbidden, word = check_forbidden_words(value)
            if contains_forbidden:
                raise serializers.ValidationError(
                    f"Nội dung chứa từ ngữ không phù hợp: '{word}'. Vui lòng sửa lại."
                )
        return value


class ReviewLikeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReviewLike
        fields = ['id', 'review', 'user', 'created_at']
        read_only_fields = ['user', 'created_at']

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class OrderReviewSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()
    order_number = serializers.SerializerMethodField()

    class Meta:
        model = OrderReview
        fields = ['id', 'order', 'user', 'rating', 'comment',
                  'images', 'status', 'created_at', 'user_name', 'order_number']
        read_only_fields = ['user', 'status', 'created_at']

    def get_user_name(self, obj):
        return obj.user.full_name or obj.user.email

    def get_order_number(self, obj):
        return f"#{obj.order.id}"

    def validate_order(self, value):
        # Kiểm tra xem người dùng hiện tại có sở hữu order này không
        request = self.context.get('request')
        if request and request.user:
            if value.user != request.user:
                raise serializers.ValidationError("Bạn chỉ có thể đánh giá đơn hàng của chính mình.")

            # Kiểm tra đơn hàng đã được nhận chưa
            if value.order_status != 'received':
                raise serializers.ValidationError("Bạn chỉ có thể đánh giá khi đã nhận đơn hàng.")

            # Kiểm tra đã đánh giá đơn hàng này chưa
            if OrderReview.objects.filter(user=request.user, order=value).exists():
                raise serializers.ValidationError("Bạn đã đánh giá đơn hàng này rồi.")

        return value

    def validate_rating(self, value):
        if not 1 <= value <= 5:
            raise serializers.ValidationError("Đánh giá phải từ 1 đến 5 sao.")
        return value

    def create(self, validated_data):
        # Tự động thêm user
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)

    def validate_comment(self, value):
        if value:
            contains_forbidden, word = check_forbidden_words(value)
            if contains_forbidden:
                raise serializers.ValidationError(
                    f"Nội dung chứa từ ngữ không phù hợp: '{word}'. Vui lòng sửa lại."
                )
        return value
