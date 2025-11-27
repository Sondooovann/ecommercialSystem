# payments/views.py
from rest_framework import viewsets, status, permissions, generics
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Payment
from .serializers import (
    PaymentSerializer,
    PaymentCreateSerializer,
    PaymentUpdateSerializer,
    PaymentMethodSerializer
)
from django.db import transaction
from django.conf import settings

class PaymentViewSet(viewsets.ModelViewSet):
    """ViewSet cho Payment model"""
    queryset = Payment.objects.all().order_by('-created_at')
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Chỉ trả về thanh toán của người dùng hiện tại trừ khi là admin"""
        user = self.request.user
        if user.role == 'admin':
            return self.queryset

        # Người dùng thông thường chỉ xem được thanh toán của đơn hàng của mình
        return self.queryset.filter(order__user=user)

    def get_serializer_class(self):
        """Sử dụng serializer phù hợp dựa trên action"""
        if self.action == 'create':
            return PaymentCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return PaymentUpdateSerializer
        return PaymentSerializer

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        """Tạo mới một thanh toán"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Lưu thanh toán
        payment = serializer.save()

        # Trả về thông tin chi tiết thanh toán
        return Response(
            PaymentSerializer(payment).data,
            status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=['post'])
    @transaction.atomic
    def confirm(self, request, pk=None):
        """Xác nhận thanh toán thành công"""
        payment = self.get_object()

        # Kiểm tra trạng thái hiện tại
        if payment.status == 'completed':
            return Response(
                {"message": "Thanh toán này đã được xác nhận trước đó"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Cập nhật trạng thái thanh toán
        payment.status = 'completed'
        payment.save(update_fields=['status', 'updated_at'])

        # Cập nhật trạng thái thanh toán của đơn hàng
        order = payment.order
        order.payment_status = 'paid'
        order.save(update_fields=['payment_status', 'updated_at'])

        return Response(
            {"message": "Thanh toán đã được xác nhận thành công"},
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['post'])
    @transaction.atomic
    def cancel(self, request, pk=None):
        """Hủy thanh toán"""
        payment = self.get_object()

        # Kiểm tra trạng thái hiện tại
        if payment.status == 'completed':
            return Response(
                {"message": "Không thể hủy thanh toán đã hoàn tất"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Cập nhật trạng thái thanh toán
        payment.status = 'failed'
        payment.save(update_fields=['status', 'updated_at'])

        return Response(
            {"message": "Thanh toán đã được hủy"},
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['post'])
    @transaction.atomic
    def refund(self, request, pk=None):
        """Hoàn tiền thanh toán"""
        payment = self.get_object()

        # Kiểm tra trạng thái hiện tại
        if payment.status != 'completed':
            return Response(
                {"message": "Chỉ có thể hoàn tiền cho thanh toán đã hoàn tất"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Cập nhật trạng thái thanh toán
        payment.status = 'refunded'
        payment.save(update_fields=['status', 'updated_at'])

        # Có thể thêm logic hoàn tiền thông qua payment gateway ở đây

        return Response(
            {"message": "Thanh toán đã được hoàn tiền"},
            status=status.HTTP_200_OK
        )


class PaymentMethodView(generics.ListAPIView):
    """View để lấy danh sách các phương thức thanh toán"""
    serializer_class = PaymentMethodSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Định nghĩa danh sách các phương thức thanh toán
        payment_methods = [
            {
                'id': 'banking',
                'name': 'Chuyển khoản ngân hàng',
                'description': 'Thanh toán bằng chuyển khoản ngân hàng',
                'icon_url': f'{settings.MEDIA_URL}payment_icons/banking.png',
                'is_available': True
            },
            {
                'id': 'momo',
                'name': 'Ví MoMo',
                'description': 'Thanh toán qua ví điện tử MoMo',
                'icon_url': f'{settings.MEDIA_URL}payment_icons/momo.png',
                'is_available': True
            },
            {
                'id': 'zalopay',
                'name': 'ZaloPay',
                'description': 'Thanh toán qua ví điện tử ZaloPay',
                'icon_url': f'{settings.MEDIA_URL}payment_icons/zalopay.png',
                'is_available': True
            },
            {
                'id': 'cod',
                'name': 'Thanh toán khi nhận hàng (COD)',
                'description': 'Thanh toán bằng tiền mặt khi nhận hàng',
                'icon_url': f'{settings.MEDIA_URL}payment_icons/cod.png',
                'is_available': True
            }
        ]

        return payment_methods


# Tạo thêm view để xử lý webhook từ các cổng thanh toán
class PaymentWebhookView(generics.GenericAPIView):
    """Webhook để xử lý callback từ các cổng thanh toán"""
    permission_classes = [permissions.AllowAny]  # Các webhook thường không yêu cầu xác thực

    def post(self, request, provider):
        """Xử lý callback từ cổng thanh toán"""
        # Kiểm tra provider hợp lệ
        if provider not in [choice[0] for choice in Payment.PROVIDER_CHOICES]:
            return Response(
                {"message": f"Không hỗ trợ cổng thanh toán: {provider}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Xử lý callback dựa trên provider
        if provider == 'momo':
            return self.handle_momo_callback(request.data)
        elif provider == 'zalopay':
            return self.handle_zalopay_callback(request.data)
        elif provider == 'banking':
            return self.handle_banking_callback(request.data)
        elif provider == 'paypal':
            return self.handle_paypal_callback(request.data)
        elif provider == 'stripe':
            return self.handle_stripe_callback(request.data)

        return Response(
            {"message": "Không thể xử lý callback"},
            status=status.HTTP_400_BAD_REQUEST
        )

    def handle_momo_callback(self, data):
        """Xử lý callback từ MoMo"""
        try:
            # Lấy thông tin thanh toán từ callback data
            transaction_id = data.get('transId')
            order_id = data.get('orderId')
            result_code = data.get('resultCode')

            # Kiểm tra kết quả
            if result_code != 0:
                return Response(
                    {"message": "Thanh toán MoMo không thành công"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Tìm thanh toán theo transaction_id hoặc order_id
            try:
                payment = Payment.objects.get(transaction_id=transaction_id)
            except Payment.DoesNotExist:
                # Nếu không tìm thấy bằng transaction_id, thử tìm qua order_id
                # Giả sử order_id được mã hóa với định dạng 'order-{order_id}'
                try:
                    order_id_number = order_id.split('-')[1]
                    payment = Payment.objects.get(order__id=order_id_number, provider='momo')
                except:
                    return Response(
                        {"message": "Không tìm thấy thanh toán phù hợp"},
                        status=status.HTTP_404_NOT_FOUND
                    )

            # Cập nhật trạng thái thanh toán
            payment.status = 'completed'
            payment.transaction_id = transaction_id
            payment.payment_data = json.dumps(data)
            payment.save()

            # Cập nhật trạng thái đơn hàng
            order = payment.order
            order.payment_status = 'paid'
            order.save(update_fields=['payment_status', 'updated_at'])

            return Response(
                {"message": "Cập nhật thanh toán thành công"},
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response(
                {"message": f"Lỗi xử lý callback MoMo: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    # Các hàm xử lý callback khác tương tự
    def handle_zalopay_callback(self, data):
        # Xử lý callback từ ZaloPay
        pass

    def handle_banking_callback(self, data):
        # Xử lý callback từ Banking
        pass

    def handle_paypal_callback(self, data):
        # Xử lý callback từ PayPal
        pass

    def handle_stripe_callback(self, data):
        # Xử lý callback từ Stripe
        pass