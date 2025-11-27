# orders/serializers.py
from rest_framework import serializers
from .models import Order, OrderItem, OrderTracking
from core.models import Address
from products.models import ProductVariant
from shops.serializers import ShopListSerializer
from django.db import transaction
from core.serializers import CustomerInfoSerializer
from django.utils import timezone



class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = [
            'id',
            'recipient_name',   # <- sửa từ full_name
            'phone',
            'province',
            'district',
            'ward',
            'street_address',
            'is_default'
        ]


class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_image = serializers.SerializerMethodField()
    variant_details = serializers.SerializerMethodField()
    shop_details = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = ['id', 'product_name', 'product_image', 'variant_details',
                  'shop_details', 'quantity', 'price', 'subtotal', 'status',
                  'created_at', 'updated_at']
        read_only_fields = fields

    def get_product_image(self, obj):
        # Lấy ảnh đại diện của sản phẩm
        thumbnail = obj.product.images.filter(is_thumbnail=True).first()
        if thumbnail:
            return thumbnail.image_url
        # Lấy ảnh đầu tiên nếu không có thumbnail
        first_image = obj.product.images.first()
        if first_image:
            return first_image.image_url
        return None

    def get_variant_details(self, obj):
        # Trả về thông tin chi tiết của biến thể
        variant = obj.variant
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

        return {
            'id': variant.id,
            'sku': variant.sku,
            'attributes': attributes,
        }

    def get_shop_details(self, obj):
        # Trả về thông tin cơ bản của cửa hàng
        return {
            'id': obj.shop.id,
            'name': obj.shop.name,
            'logo': obj.shop.logo
        }


class OrderTrackingSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source='created_by.full_name', read_only=True)

    class Meta:
        model = OrderTracking
        fields = ['id', 'status', 'note', 'created_by_name', 'created_at']
        read_only_fields = fields


class OrderDetailSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    address = AddressSerializer(read_only=True)
    tracking_history = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = ['id', 'user', 'address', 'total_amount', 'shipping_fee',
                  'discount_amount', 'payment_method', 'payment_status',
                  'order_status', 'notes', 'items', 'tracking_history',
                  'created_at', 'updated_at']
        read_only_fields = fields

    def get_tracking_history(self, obj):
        tracking_items = obj.tracking_items.all().order_by('-created_at')
        return OrderTrackingSerializer(tracking_items, many=True).data


class OrderListSerializer(serializers.ModelSerializer):
    items_count = serializers.SerializerMethodField()
    first_product = serializers.SerializerMethodField()
    customer = CustomerInfoSerializer(source='user', read_only=True)
    class Meta:
        model = Order

        fields = ['id', 'total_amount', 'payment_method', 'payment_status','customer',
                  'order_status', 'items_count', 'first_product', 'created_at']
        read_only_fields = fields

    def get_items_count(self, obj):
        return obj.items.count()

    def get_first_product(self, obj):
        first_item = obj.items.first()
        if not first_item:
            return None

        # Lấy ảnh sản phẩm
        product = first_item.product
        image_url = None
        thumbnail = product.images.filter(is_thumbnail=True).first()
        if thumbnail:
            image_url = thumbnail.image_url
        else:
            first_image = product.images.first()
            if first_image:
                image_url = first_image.image_url

        return {
            'name': product.name,
            'image': image_url,
            'quantity': first_item.quantity,
            'more_items': obj.items.count() > 1
        }


# orders/serializers.py
class CreateOrderSerializer(serializers.Serializer):
    address_id = serializers.IntegerField()
    payment_method = serializers.ChoiceField(choices=Order.PAYMENT_METHOD_CHOICES)
    notes = serializers.CharField(required=False, allow_blank=True)
    cart_item_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=True,
        help_text="Danh sách ID của các mục trong giỏ hàng cần thanh toán"
    )

    def validate_address_id(self, value):
        user = self.context['request'].user
        try:
            address = Address.objects.get(id=value, user=user)
            return value
        except Address.DoesNotExist:
            raise serializers.ValidationError("Địa chỉ không tồn tại hoặc không thuộc về người dùng này")

    def validate_cart_item_ids(self, value):
        user = self.context['request'].user

        # Kiểm tra xem các ID có hợp lệ không
        from cart.models import CartItem, Cart

        if not value:
            raise serializers.ValidationError("Vui lòng chọn ít nhất một sản phẩm để thanh toán")

        # Lấy giỏ hàng của người dùng
        cart = Cart.objects.filter(user=user).first()
        if not cart:
            raise serializers.ValidationError("Giỏ hàng không tồn tại")

        # Kiểm tra xem tất cả các ID có thuộc về giỏ hàng của người dùng không
        valid_ids = set(cart.items.values_list('id', flat=True))
        for item_id in value:
            if item_id not in valid_ids:
                raise serializers.ValidationError(
                    f"Mục giỏ hàng với ID {item_id} không tồn tại hoặc không thuộc về bạn")

        return value

    @transaction.atomic
    def create(self, validated_data):
        user = self.context['request'].user
        address_id = validated_data.get('address_id')
        payment_method = validated_data.get('payment_method')
        notes = validated_data.get('notes', '')
        cart_item_ids = validated_data.get('cart_item_ids', [])

        # Lấy giỏ hàng của người dùng
        from cart.models import Cart, CartItem
        cart = Cart.objects.filter(user=user).first()

        if not cart:
            raise serializers.ValidationError("Giỏ hàng không tồn tại")

        # Lấy các mục đã chọn từ giỏ hàng
        selected_items = CartItem.objects.filter(
            id__in=cart_item_ids,
            cart=cart
        ).select_related(
            'variant',
            'variant__product',
            'variant__product__shop'
        )

        if not selected_items:
            raise serializers.ValidationError("Không tìm thấy sản phẩm nào đã chọn trong giỏ hàng")

        # Kiểm tra tồn kho cho tất cả các mục đã chọn
        from .utils import check_variant_availability
        
        for cart_item in selected_items:
            variant = cart_item.variant
            is_available, error_message = check_variant_availability(variant, cart_item.quantity)
            if not is_available:
                raise serializers.ValidationError(error_message)

        # Tính tổng tiền cho các mục đã chọn
        total_amount = 0
        shipping_fee = 30000  # Có thể tính toán phí vận chuyển dựa trên logic nghiệp vụ
        discount_amount = 0  # Có thể áp dụng giảm giá nếu có

        for cart_item in selected_items:
            variant = cart_item.variant
            # Lấy giá sản phẩm
            price = variant.sale_price if variant.sale_price else variant.price
            if not price:
                product = variant.product
                price = product.sale_price if product.sale_price else product.price

            # Tính tổng tiền
            subtotal = price * cart_item.quantity
            total_amount += subtotal

        # Cộng phí vận chuyển, trừ giảm giá
        final_amount = total_amount + shipping_fee - discount_amount

        # Tạo đơn hàng
        address = Address.objects.get(id=address_id)
        order = Order.objects.create(
            user=user,
            address=address,
            total_amount=final_amount,
            shipping_fee=shipping_fee,
            discount_amount=discount_amount,
            payment_method=payment_method,
            notes=notes
        )

        # Tạo các mục đơn hàng
        for cart_item in selected_items:
            variant = cart_item.variant
            product = variant.product
            shop = product.shop

            # Lấy giá sản phẩm
            price = variant.sale_price if variant.sale_price else variant.price
            if not price:
                price = product.sale_price if product.sale_price else product.price

            # Tính tổng tiền của mục
            subtotal = price * cart_item.quantity

            # Tạo mục đơn hàng
            OrderItem.objects.create(
                order=order,
                product=product,
                variant=variant,
                shop=shop,
                quantity=cart_item.quantity,
                price=price,
                subtotal=subtotal
            )

            # Sử dụng các hàm tiện ích để cập nhật tồn kho
            from .utils import decrease_product_stock, update_product_status_based_on_variants
            
            # Cập nhật tồn kho của variant
            variant.stock -= cart_item.quantity
            variant.save(update_fields=['stock'])
            
            # Cập nhật tồn kho và trạng thái của sản phẩm chính
            decrease_product_stock(product, cart_item.quantity)
            
            # Cập nhật trạng thái sản phẩm dựa trên tồn kho của tất cả variant
            update_product_status_based_on_variants(product)

        # Tạo bản ghi theo dõi đơn hàng đầu tiên
        OrderTracking.objects.create(
            order=order,
            status='pending',
            note="Đơn hàng đã được tạo",
            created_by=user
        )

        # Xóa các mục đã chọn khỏi giỏ hàng
        selected_items.delete()

        return order

# orders/serializers.py
# orders/serializers.py
class BulkUpdateOrderStatusSerializer(serializers.Serializer):
    order_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=True,
        help_text="Danh sách ID của các đơn hàng cần cập nhật trạng thái"
    )
    status = serializers.ChoiceField(
        choices=Order.ORDER_STATUS_CHOICES,
        required=True,
        help_text="Trạng thái mới cho tất cả đơn hàng được chọn"
    )
    note = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Ghi chú cho việc cập nhật trạng thái"
    )

    def validate_order_ids(self, value):
        """Kiểm tra xem tất cả các ID đều hợp lệ và thuộc về shop của người dùng"""
        if not value:
            raise serializers.ValidationError("Vui lòng chọn ít nhất một đơn hàng để cập nhật")

        user = self.context['request'].user

        # Kiểm tra quyền truy cập
        if user.role not in ['shop_owner', 'admin']:
            raise serializers.ValidationError("Bạn không có quyền cập nhật đơn hàng")

        # Kiểm tra shop_id
        shop_id = self.context.get('shop_id')
        if not shop_id and user.role == 'shop_owner':
            raise serializers.ValidationError("Cần có shop_id để cập nhật đơn hàng")

        # Xác minh tất cả đơn hàng đều tồn tại và thuộc về shop
        valid_orders = []
        invalid_orders = []
        cancelled_orders = []

        for order_id in value:
            try:
                if user.role == 'admin':
                    # Admin có thể cập nhật bất kỳ đơn hàng nào (trừ đơn hàng đã hủy)
                    order = Order.objects.get(id=order_id)

                    # Kiểm tra xem đơn hàng đã bị hủy chưa
                    if order.order_status == 'cancelled':
                        cancelled_orders.append(order_id)
                    else:
                        valid_orders.append(order_id)
                else:
                    # Người bán chỉ có thể cập nhật đơn hàng có sản phẩm từ shop của họ
                    # Kiểm tra xem đơn hàng có tồn tại không
                    try:
                        order = Order.objects.get(id=order_id)

                        # Kiểm tra xem đơn hàng có thuộc về shop không
                        shop_items = order.items.filter(shop_id=shop_id).exists()

                        if not shop_items:
                            invalid_orders.append(order_id)
                        elif order.order_status == 'cancelled':
                            cancelled_orders.append(order_id)
                        else:
                            valid_orders.append(order_id)
                    except Order.DoesNotExist:
                        invalid_orders.append(order_id)
            except Order.DoesNotExist:
                invalid_orders.append(order_id)

        error_messages = []

        if invalid_orders:
            error_messages.append(
                f"Các đơn hàng sau không tồn tại hoặc không thuộc về shop của bạn: {', '.join(map(str, invalid_orders))}"
            )

        if cancelled_orders:
            error_messages.append(
                f"Các đơn hàng sau đã bị hủy và không thể cập nhật: {', '.join(map(str, cancelled_orders))}"
            )

        if error_messages:
            raise serializers.ValidationError(error_messages)

        return valid_orders

    def validate(self, data):
        """Kiểm tra tính hợp lệ của dữ liệu"""
        # Kiểm tra trường hợp cụ thể: không cho phép cập nhật từ trạng thái hủy sang trạng thái khác
        status = data.get('status')

        # Nếu trạng thái mới là 'cancelled', không cần kiểm tra thêm
        # vì đơn hàng đã bị hủy sẽ bị loại bỏ ở validate_order_ids

        return data

    @transaction.atomic
    def create(self, validated_data):
        """Cập nhật trạng thái cho nhiều đơn hàng"""
        user = self.context['request'].user
        order_ids = validated_data.get('order_ids', [])
        new_status = validated_data.get('status')
        note = validated_data.get('note', '')
        shop_id = self.context.get('shop_id')

        # Lấy tất cả đơn hàng cần cập nhật
        if user.role == 'admin':
            # Lấy tất cả đơn hàng hợp lệ (loại bỏ đơn hàng đã hủy)
            orders = Order.objects.filter(
                id__in=order_ids
            ).exclude(
                order_status='cancelled'
            )
        else:
            # Lấy đơn hàng thuộc shop và chưa bị hủy
            orders = Order.objects.filter(
                id__in=order_ids,
                items__shop_id=shop_id
            ).exclude(
                order_status='cancelled'
            ).distinct()

        # Tạo danh sách các đối tượng OrderTracking để bulk create
        tracking_items = []
        updated_orders = []
        updated_order_items = []

        for order in orders:
            # Cập nhật trạng thái đơn hàng
            order.order_status = new_status
            order.updated_at = timezone.now()
            updated_orders.append(order)

            # Tạo đối tượng tracking
            tracking_items.append(
                OrderTracking(
                    order=order,
                    status=new_status,
                    note=note,
                    created_by=user
                )
            )

            # Nếu là người bán, chỉ cập nhật các mục của shop của họ
            if user.role == 'shop_owner':
                order_items = order.items.filter(shop_id=shop_id)
            else:
                order_items = order.items.all()

            # Cập nhật trạng thái các mục đơn hàng
            for item in order_items:
                item.status = new_status
                item.updated_at = timezone.now()
                updated_order_items.append(item)

        # Bulk update đơn hàng
        if updated_orders:
            Order.objects.bulk_update(updated_orders, ['order_status', 'updated_at'])

        # Bulk update các mục đơn hàng
        if updated_order_items:
            OrderItem.objects.bulk_update(updated_order_items, ['status', 'updated_at'])

        # Bulk create các tracking item
        if tracking_items:
            OrderTracking.objects.bulk_create(tracking_items)

        # Trả về một đối tượng để biểu thị kết quả
        return {
            'count': len(updated_orders),
            'order_ids': [order.id for order in updated_orders],
            # Chỉ trả về ID của những đơn hàng thực sự được cập nhật
            'status': new_status,
            'updated_at': timezone.now()
        }

class UpdateOrderStatusSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=Order.ORDER_STATUS_CHOICES)
    note = serializers.CharField(required=False, allow_blank=True)

    @transaction.atomic
    def update(self, instance, validated_data):
        user = self.context['request'].user
        new_status = validated_data.get('status')
        note = validated_data.get('note', '')

        # Kiểm tra quyền truy cập
        if user.role == 'customer' and new_status not in ['cancelled']:
            raise serializers.ValidationError("Người dùng không có quyền cập nhật trạng thái này")

        # Cập nhật trạng thái đơn hàng
        instance.order_status = new_status
        instance.save(update_fields=['order_status', 'updated_at'])

        # Tạo bản ghi theo dõi đơn hàng
        OrderTracking.objects.create(
            order=instance,
            status=new_status,
            note=note,
            created_by=user
        )

        # Cập nhật trạng thái của tất cả các mục đơn hàng nếu cần
        if user.role != 'customer':  # Người bán hoặc admin mới có thể cập nhật trạng thái mục
            instance.items.all().update(status=new_status)

        return instance


class UpdateOrderItemStatusSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=OrderItem.STATUS_CHOICES)
    note = serializers.CharField(required=False, allow_blank=True)

    @transaction.atomic
    def update(self, instance, validated_data):
        user = self.context['request'].user
        new_status = validated_data.get('status')
        note = validated_data.get('note', '')

        # Kiểm tra quyền truy cập
        if user.role == 'customer' and new_status not in ['cancelled']:
            raise serializers.ValidationError("Người dùng không có quyền cập nhật trạng thái này")

        # Kiểm tra xem người dùng có phải là chủ cửa hàng
        if user.role == 'shop_owner' and instance.shop.owner != user:
            raise serializers.ValidationError("Bạn không phải là chủ cửa hàng của sản phẩm này")

        # Cập nhật trạng thái mục đơn hàng
        instance.status = new_status
        instance.save(update_fields=['status', 'updated_at'])

        # Tạo bản ghi theo dõi đơn hàng
        OrderTracking.objects.create(
            order=instance.order,
            status=new_status,
            note=f"Cập nhật trạng thái cho sản phẩm {instance.product.name}: {note}",
            created_by=user
        )

        # Kiểm tra xem tất cả các mục trong đơn hàng có cùng trạng thái không
        order = instance.order
        items_status_set = set(order.items.values_list('status', flat=True))

        # Nếu tất cả các mục có cùng trạng thái, cập nhật trạng thái đơn hàng
        if len(items_status_set) == 1:
            order.order_status = new_status
            order.save(update_fields=['order_status', 'updated_at'])

        return instance


# orders/serializers.py

class OrderDetailForShopSerializer(serializers.ModelSerializer):
    """Serializer chi tiết đơn hàng cho shop bao gồm thông tin khách hàng"""
    items = OrderItemSerializer(many=True, read_only=True)
    address = AddressSerializer(read_only=True)
    tracking_history = serializers.SerializerMethodField()
    customer = CustomerInfoSerializer(source='user', read_only=True)

    class Meta:
        model = Order
        fields = [
            'id',
            'customer',  # Thông tin khách hàng
            'address',
            'total_amount',
            'shipping_fee',
            'discount_amount',
            'payment_method',
            'payment_status',
            'order_status',
            'notes',
            'items',
            'tracking_history',
            'created_at',
            'updated_at'
        ]
        read_only_fields = fields

    def get_tracking_history(self, obj):
        tracking_items = obj.tracking_items.all().order_by('-created_at')
        return OrderTrackingSerializer(tracking_items, many=True).data


class OrderListForShopSerializer(serializers.ModelSerializer):
    """Serializer danh sách đơn hàng cho shop bao gồm thông tin khách hàng tóm tắt"""
    items_count = serializers.SerializerMethodField()
    first_product = serializers.SerializerMethodField()
    customer = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            'id',
            'customer',  # Thông tin khách hàng tóm tắt
            'total_amount',
            'payment_method',
            'payment_status',
            'order_status',
            'items_count',
            'first_product',
            'created_at'
        ]
        read_only_fields = fields

    def get_items_count(self, obj):
        return obj.items.count()

    def get_first_product(self, obj):
        first_item = obj.items.first()
        if not first_item:
            return None

        # Lấy ảnh sản phẩm
        product = first_item.product
        image_url = None
        thumbnail = product.images.filter(is_thumbnail=True).first()
        if thumbnail:
            image_url = thumbnail.image_url
        else:
            first_image = product.images.first()
            if first_image:
                image_url = first_image.image_url

        return {
            'name': product.name,
            'image': image_url,
            'quantity': first_item.quantity,
            'more_items': obj.items.count() > 1
        }

    def get_customer(self, obj):
        """Trả về thông tin tóm tắt về khách hàng"""
        return {
            'id': obj.user.id,
            'full_name': obj.user.full_name,
            'phone': obj.user.phone,
            'email': obj.user.email
        }


# orders/serializers.py
from rest_framework import serializers
from .models import Order, OrderTracking
from django.db import transaction
from django.utils import timezone


class CancelOrderSerializer(serializers.Serializer):
    reason = serializers.ChoiceField(
        choices=[
            ('change_mind', 'Đổi ý không muốn mua nữa'),
            ('found_better_deal', 'Tìm thấy ưu đãi tốt hơn ở nơi khác'),
            ('ordered_wrong_item', 'Đặt nhầm sản phẩm'),
            ('shipping_too_long', 'Thời gian giao hàng quá lâu'),
            ('financial_reasons', 'Lý do tài chính'),
            ('other', 'Lý do khác')
        ],
        required=True,
        help_text="Lý do hủy đơn hàng"
    )
    note = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=500,
        help_text="Ghi chú thêm về việc hủy đơn hàng"
    )

    def validate(self, data):
        """Kiểm tra xem đơn hàng có thể hủy được không"""
        order = self.instance

        # Kiểm tra trạng thái hiện tại của đơn hàng
        cancellable_statuses = ['pending', 'confirmed']
        if order.order_status not in cancellable_statuses:
            raise serializers.ValidationError(
                f"Không thể hủy đơn hàng trong trạng thái '{order.get_order_status_display()}'. "
                f"Chỉ có thể hủy đơn hàng ở trạng thái 'Chờ xác nhận' hoặc 'Đã xác nhận'."
            )

        # Kiểm tra trạng thái thanh toán nếu đã thanh toán
        if order.payment_status == 'paid':
            # Có thể thêm kiểm tra thời gian từ khi thanh toán
            # Ví dụ: Nếu thanh toán quá 24h thì không cho hủy
            # Nhưng ở đây, chúng ta vẫn cho phép hủy đơn đã thanh toán
            pass

        return data

    @transaction.atomic
    def update(self, instance, validated_data):
        """Thực hiện hủy đơn hàng"""
        user = self.context['request'].user
        reason = validated_data.get('reason')
        note = validated_data.get('note', '')

        # Tạo nội dung ghi chú dựa trên lý do
        reason_display = dict(self.fields['reason'].choices)[reason]
        cancel_note = f"Lý do: {reason_display}"
        if note:
            cancel_note += f" - {note}"

        # Cập nhật trạng thái đơn hàng
        instance.order_status = 'cancelled'
        instance.updated_at = timezone.now()
        instance.save(update_fields=['order_status', 'updated_at'])

        # Tạo bản ghi theo dõi đơn hàng
        OrderTracking.objects.create(
            order=instance,
            status='cancelled',
            note=cancel_note,
            created_by=user
        )

        # Cập nhật trạng thái của tất cả các mục đơn hàng
        instance.items.all().update(status='cancelled', updated_at=timezone.now())

        # Khôi phục tồn kho cho các sản phẩm
        for item in instance.items.all():
            variant = item.variant
            product = item.product
            
            if variant:
                # Sử dụng các hàm tiện ích để khôi phục tồn kho
                from .utils import increase_product_stock, update_product_status_based_on_variants
                
                # Khôi phục tồn kho của variant
                variant.stock += item.quantity
                variant.save(update_fields=['stock'])
                
                # Khôi phục tồn kho và cập nhật trạng thái của sản phẩm chính
                increase_product_stock(product, item.quantity)
                
                # Cập nhật trạng thái sản phẩm dựa trên tồn kho của tất cả variant
                update_product_status_based_on_variants(product)

        # Nếu đơn hàng đã thanh toán, đánh dấu cần hoàn tiền
        if instance.payment_status == 'paid':
            instance.payment_status = 'refunding'
            instance.save(update_fields=['payment_status'])

            # Có thể thêm logic tạo yêu cầu hoàn tiền ở đây
            from payments.models import Payment
            payments = Payment.objects.filter(order=instance, status='completed')
            for payment in payments:
                payment.status = 'refunding'
                payment.save(update_fields=['status', 'updated_at'])

        return instance

# orders/serializers.py
class ConfirmOrderReceivedSerializer(serializers.Serializer):
    note = serializers.CharField(required=False, allow_blank=True, max_length=500,
                                help_text="Ghi chú khi nhận hàng (tùy chọn)")

    def validate(self, data):
        """Kiểm tra xem đơn hàng có thể được xác nhận đã nhận hay không"""
        order = self.instance

        # Khách hàng chỉ có thể xác nhận đã nhận khi đơn hàng đang trong trạng thái đang giao
        if order.order_status != 'delivered':
            raise serializers.ValidationError(
                f"Không thể xác nhận đã nhận đơn hàng trong trạng thái '{order.get_order_status_display()}'. "
                f"Chỉ có thể xác nhận khi đơn hàng đang trong trạng thái 'Đã giao hàng'."
            )

        # Xác minh người dùng là chủ của đơn hàng
        user = self.context['request'].user
        if order.user != user:
            raise serializers.ValidationError("Bạn không phải là chủ của đơn hàng này.")

        return data

    @transaction.atomic
    def update(self, instance, validated_data):
        """Thực hiện cập nhật trạng thái đơn hàng thành đã nhận"""
        user = self.context['request'].user
        note = validated_data.get('note', '')

        # Tạo nội dung ghi chú
        confirm_note = "Khách hàng đã xác nhận nhận được hàng"
        if note:
            confirm_note += f" - {note}"

        # Cập nhật trạng thái đơn hàng
        instance.order_status = 'received'
        instance.updated_at = timezone.now()
        instance.save(update_fields=['order_status', 'updated_at'])

        # Tạo bản ghi theo dõi đơn hàng
        OrderTracking.objects.create(
            order=instance,
            status='received',
            note=confirm_note,
            created_by=user
        )
        # Cập nhật trạng thái của tất cả các mục đơn hàng
        instance.items.all().update(status='received', updated_at=timezone.now())
        # # Cập nhật trạng thái thanh toán nếu là thanh toán khi nhận hàng (COD)
        # if instance.payment_method == 'cod' and instance.payment_status != 'paid':
        #     instance.payment_status = 'paid'
        #     instance.save(update_fields=['payment_status'])
        #
        #     # Có thể thêm logic tạo bản ghi thanh toán ở đây
        #     from payments.models import Payment
        #     Payment.objects.create(
        #         order=instance,
        #         user=user,
        #         amount=instance.total_amount,
        #         payment_method='cod',
        #         status='completed',
        #         transaction_id=f"COD-{instance.id}-{timezone.now().strftime('%Y%m%d%H%M%S')}",
        #         transaction_data={"confirmed_by_customer": True}
        #     )

        return instance

