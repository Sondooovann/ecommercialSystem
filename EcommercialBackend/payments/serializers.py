# payments/serializers.py
from rest_framework import serializers
from .models import Payment
from orders.serializers import OrderListSerializer
import json

class PaymentSerializer(serializers.ModelSerializer):
    order_details = OrderListSerializer(source='order', read_only=True)
    payment_data_json = serializers.SerializerMethodField()

    class Meta:
        model = Payment
        fields = ['id', 'order', 'order_details', 'amount', 'provider',
                  'transaction_id', 'status', 'payment_data', 'payment_data_json',
                  'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
        extra_kwargs = {
            'payment_data': {'write_only': True}
        }

    def get_payment_data_json(self, obj):
        """Chuyển đổi payment_data từ JSON string sang dictionary"""
        if not obj.payment_data:
            return None
        try:
            return json.loads(obj.payment_data)
        except:
            return None


class PaymentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ['order', 'amount', 'provider', 'transaction_id', 'payment_data']

    def validate_order(self, value):
        """Kiểm tra quyền truy cập vào đơn hàng"""
        user = self.context['request'].user
        if value.user != user and user.role != 'admin':
            raise serializers.ValidationError("Bạn không có quyền tạo thanh toán cho đơn hàng này")

        # Kiểm tra trạng thái thanh toán của đơn hàng
        if value.payment_status == 'paid':
            raise serializers.ValidationError("Đơn hàng này đã được thanh toán")

        return value

    def validate(self, data):
        """Kiểm tra dữ liệu thanh toán"""
        # Kiểm tra số tiền thanh toán
        order = data.get('order')
        amount = data.get('amount')

        if order and amount and amount != order.total_amount:
            raise serializers.ValidationError({
                "amount": f"Số tiền thanh toán ({amount}) không khớp với tổng tiền đơn hàng ({order.total_amount})"
            })

        return data


class PaymentUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ['status', 'transaction_id', 'payment_data']
        extra_kwargs = {
            'status': {'required': True},
            'transaction_id': {'required': False},
            'payment_data': {'required': False}
        }

    def update(self, instance, validated_data):
        """Cập nhật trạng thái thanh toán và đơn hàng"""
        # Cập nhật thanh toán
        instance = super().update(instance, validated_data)

        # Cập nhật trạng thái thanh toán của đơn hàng nếu thanh toán hoàn tất
        if instance.status == 'completed':
            order = instance.order
            order.payment_status = 'paid'
            order.save(update_fields=['payment_status', 'updated_at'])

        return instance


class PaymentMethodSerializer(serializers.Serializer):
    """Serializer để lấy thông tin các phương thức thanh toán"""
    id = serializers.CharField()
    name = serializers.CharField()
    description = serializers.CharField()
    icon_url = serializers.URLField()
    is_available = serializers.BooleanField()