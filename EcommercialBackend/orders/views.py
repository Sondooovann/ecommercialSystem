# orders/views.py
from core.views import IsAdminUser
from products.models import Product
from .models import Order, OrderItem, OrderTracking
from .serializers import (
    OrderListSerializer, OrderDetailSerializer, CreateOrderSerializer,
    UpdateOrderStatusSerializer, UpdateOrderItemStatusSerializer, ConfirmOrderReceivedSerializer
)
from core.permission import IsShopOwner, IsCustomer
from django.db.models import Q, Prefetch, F, Sum

# orders/views.py
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework import status, permissions
from .serializers import BulkUpdateOrderStatusSerializer
from shops.models import Shop
from core.permission import IsShopOwner

# orders/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.db.models import Q, Sum, Count, F
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.core.paginator import Paginator

from .models import Order, OrderItem, OrderTracking
from products.models import Product


class AdminOrderListView(APIView):
    """API cho admin xem danh sách tất cả đơn hàng"""
    permission_classes = [IsAdminUser]

    def get(self, request):
        """Lấy danh sách tất cả đơn hàng với các bộ lọc"""
        # Lọc theo tham số truy vấn
        status_filter = request.query_params.get('status')
        search_query = request.query_params.get('search')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        user_id = request.query_params.get('user_id')
        shop_id = request.query_params.get('shop_id')
        payment_status = request.query_params.get('payment_status')
        order_by = request.query_params.get('order_by', '-created_at')

        # Bắt đầu truy vấn
        orders = Order.objects.all()

        # Áp dụng bộ lọc
        if status_filter:
            orders = orders.filter(order_status=status_filter)

        if search_query:
            orders = orders.filter(
                Q(id__icontains=search_query) |
                Q(user__email__icontains=search_query) |
                Q(user__full_name__icontains=search_query) |
                Q(items__product__name__icontains=search_query) |
                Q(address__full_name__icontains=search_query) |
                Q(address__phone__icontains=search_query)
            ).distinct()

        if start_date:
            orders = orders.filter(created_at__gte=start_date)

        if end_date:
            orders = orders.filter(created_at__lte=end_date)

        if user_id:
            orders = orders.filter(user_id=user_id)

        if shop_id:
            orders = orders.filter(items__shop_id=shop_id).distinct()

        if payment_status:
            orders = orders.filter(payment_status=payment_status)

        # Sắp xếp
        valid_order_fields = ['created_at', '-created_at', 'updated_at', '-updated_at',
                              'total_price', '-total_price']
        if order_by in valid_order_fields:
            orders = orders.order_by(order_by)
        else:
            orders = orders.order_by('-created_at')

        # Phân trang
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 10))

        paginator = Paginator(orders, page_size)
        total_count = paginator.count

        try:
            orders_page = paginator.page(page)
        except Exception:
            orders_page = paginator.page(1)

        serializer = OrderListSerializer(orders_page, many=True)

        return Response({
            'status': 'success',
            'message': 'Đã lấy danh sách đơn hàng thành công',
            'data': {
                'orders': serializer.data,
                'pagination': {
                    'total': total_count,
                    'page': page,
                    'page_size': page_size,
                    'total_pages': paginator.num_pages
                }
            }
        }, status=status.HTTP_200_OK)


class AdminOrderDetailView(APIView):
    """API cho admin xem chi tiết đơn hàng"""
    permission_classes = [IsAdminUser]

    def get(self, request, order_id):
        """Lấy chi tiết đơn hàng"""
        order = get_object_or_404(Order, id=order_id)

        # Tải trước các dữ liệu liên quan
        order = Order.objects.prefetch_related(
            'items',
            'items__product',
            'items__product__images',
            'items__variant',
            'items__variant__attribute_values',
            'items__variant__attribute_values__attribute_value',
            'items__variant__attribute_values__attribute_value__attribute',
            'items__shop',
            'tracking_items',
            'tracking_items__created_by'
        ).select_related('user', 'address').get(id=order.id)

        serializer = OrderDetailSerializer(order)

        return Response({
            'status': 'success',
            'message': 'Đã lấy chi tiết đơn hàng thành công',
            'data': serializer.data
        }, status=status.HTTP_200_OK)


class AdminUpdateOrderStatusView(APIView):
    """API cho admin cập nhật trạng thái đơn hàng"""
    permission_classes = [IsAdminUser]

    def put(self, request, order_id):
        """Cập nhật trạng thái đơn hàng"""
        order = get_object_or_404(Order, id=order_id)

        serializer = UpdateOrderStatusSerializer(
            instance=order,
            data=request.data,
            context={'request': request}
        )

        if serializer.is_valid():
            updated_order = serializer.save()

            # Trả về thông tin đơn hàng đã cập nhật
            order_serializer = OrderDetailSerializer(updated_order)

            return Response({
                'status': 'success',
                'message': 'Đã cập nhật trạng thái đơn hàng thành công',
                'data': order_serializer.data
            }, status=status.HTTP_200_OK)

        return Response({
            'status': 'error',
            'message': 'Không thể cập nhật trạng thái đơn hàng',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class AdminUpdateOrderItemStatusView(APIView):
    """API cho admin cập nhật trạng thái của một mục đơn hàng"""
    permission_classes = [IsAdminUser]

    def put(self, request, item_id):
        """Cập nhật trạng thái mục đơn hàng"""
        order_item = get_object_or_404(OrderItem, id=item_id)

        serializer = UpdateOrderItemStatusSerializer(
            instance=order_item,
            data=request.data,
            context={'request': request}
        )

        if serializer.is_valid():
            old_status = order_item.status
            new_status = request.data.get('status')

            updated_item = serializer.save()

            # Cập nhật sold_count nếu cần
            completed_statuses = ['delivered', 'received', 'received_reviewed']

            if new_status in completed_statuses and old_status not in completed_statuses:
                Product.objects.filter(pk=order_item.product.pk).update(
                    sold_count=F('sold_count') + order_item.quantity
                )
                if updated_item.order.payment_status != 'success':
                    updated_item.order.payment_status = 'success'
                    updated_item.order.save(update_fields=['payment_status'])

            elif old_status in completed_statuses and new_status in ['cancelled', 'returned']:
                Product.objects.filter(pk=order_item.product.pk).update(
                    sold_count=F('sold_count') - order_item.quantity
                )

            # Trả về thông tin đơn hàng đã cập nhật
            order_serializer = OrderDetailSerializer(updated_item.order)

            return Response({
                'status': 'success',
                'message': 'Đã cập nhật trạng thái mục đơn hàng thành công',
                'data': order_serializer.data
            }, status=status.HTTP_200_OK)

        return Response({
            'status': 'error',
            'message': 'Không thể cập nhật trạng thái mục đơn hàng',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class AdminOrderAnalyticsView(APIView):
    """API cho admin xem thống kê về đơn hàng"""
    permission_classes = [IsAdminUser]

    def get(self, request):
        """Lấy dữ liệu thống kê đơn hàng"""
        # Lọc theo thời gian nếu có
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        # Bắt đầu truy vấn
        orders_query = Order.objects.all()

        if start_date:
            orders_query = orders_query.filter(created_at__gte=start_date)

        if end_date:
            orders_query = orders_query.filter(created_at__lte=end_date)

        # Thống kê tổng quan
        total_orders = orders_query.count()
        total_revenue = orders_query.aggregate(Sum('total_price'))['total_price__sum'] or 0

        # Thống kê theo trạng thái
        status_stats = orders_query.values('order_status').annotate(
            count=Count('id'),
            total=Sum('total_price')
        ).order_by('order_status')

        # Thống kê theo phương thức thanh toán
        payment_stats = orders_query.values('payment_method').annotate(
            count=Count('id'),
            total=Sum('total_price')
        ).order_by('payment_method')

        # Thống kê theo trạng thái thanh toán
        payment_status_stats = orders_query.values('payment_status').annotate(
            count=Count('id'),
            total=Sum('total_price')
        ).order_by('payment_status')

        # Doanh thu theo ngày (30 ngày gần nhất)
        end_date = timezone.now().date()
        start_date = end_date - timezone.timedelta(days=29)

        daily_orders = []

        for i in range(30):
            current_date = start_date + timezone.timedelta(days=i)
            next_date = current_date + timezone.timedelta(days=1)

            daily_data = orders_query.filter(
                created_at__gte=current_date,
                created_at__lt=next_date
            ).aggregate(
                count=Count('id'),
                revenue=Sum('total_price')
            )

            daily_orders.append({
                'date': current_date.strftime('%Y-%m-%d'),
                'count': daily_data['count'] or 0,
                'revenue': daily_data['revenue'] or 0
            })

        return Response({
            'status': 'success',
            'message': 'Đã lấy thống kê đơn hàng thành công',
            'data': {
                'summary': {
                    'total_orders': total_orders,
                    'total_revenue': total_revenue,
                },
                'status_statistics': status_stats,
                'payment_method_statistics': payment_stats,
                'payment_status_statistics': payment_status_stats,
                'daily_orders': daily_orders
            }
        }, status=status.HTTP_200_OK)


class AdminCreateOrderTrackingView(APIView):
    """API cho admin thêm thông tin theo dõi đơn hàng"""
    permission_classes = [IsAdminUser]

    def post(self, request, order_id):
        """Thêm thông tin theo dõi đơn hàng"""
        order = get_object_or_404(Order, id=order_id)

        # Tạo tracking item mới
        try:
            tracking = OrderTracking.objects.create(
                order=order,
                status=request.data.get('status'),
                note=request.data.get('note', ''),
                created_by=request.user
            )

            # Nếu cũng cần cập nhật trạng thái đơn hàng
            if request.data.get('update_order_status', False):
                order.order_status = request.data.get('status')
                order.save()

            # Trả về thông tin đơn hàng đã cập nhật
            order_serializer = OrderDetailSerializer(order)

            return Response({
                'status': 'success',
                'message': 'Đã thêm thông tin theo dõi đơn hàng thành công',
                'data': order_serializer.data
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({
                'status': 'error',
                'message': f'Không thể thêm thông tin theo dõi đơn hàng: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)


class AdminBulkDeleteOrderView(APIView):
    """API cho admin xóa nhiều đơn hàng cùng lúc"""
    permission_classes = [IsAdminUser]

    def post(self, request):
        """Xóa nhiều đơn hàng theo danh sách ID"""
        order_ids = request.data.get('order_ids', [])

        if not order_ids:
            return Response({
                'status': 'error',
                'message': 'Vui lòng cung cấp danh sách ID đơn hàng cần xóa'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Lọc các đơn hàng cần xóa
        orders = Order.objects.filter(id__in=order_ids)
        found_ids = list(orders.values_list('id', flat=True))

        # Kiểm tra các đơn hàng không tồn tại
        not_found_ids = list(set(order_ids) - set(found_ids))

        # Đếm số đơn hàng đã xóa
        count = len(found_ids)

        # Thực hiện xóa
        orders.delete()

        return Response({
            'status': 'success',
            'message': f'Đã xóa {count} đơn hàng thành công',
            'data': {
                'deleted_count': count,
                'deleted_ids': found_ids,
                'not_found_ids': not_found_ids
            }
        }, status=status.HTTP_200_OK)


class BulkUpdateOrderStatusView(APIView):
    """API để shop cập nhật trạng thái nhiều đơn hàng cùng lúc"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = request.user
        shop_id = request.query_params.get('shop_id')

        # Kiểm tra shop_id nếu là shop_owner
        if user.role == 'shop_owner':
            if not shop_id:
                return Response({
                    'status': 'error',
                    'message': 'Vui lòng cung cấp shop_id để cập nhật đơn hàng'
                }, status=status.HTTP_400_BAD_REQUEST)
            try:
                shop = Shop.objects.get(id=shop_id, owner=user)
            except Shop.DoesNotExist:
                return Response({
                    'status': 'error',
                    'message': 'Bạn không phải là chủ sở hữu của shop này'
                }, status=status.HTTP_403_FORBIDDEN)
        else:
            shop = None  # Admin có thể cập nhật tất cả

        # Tạo context với shop_id nếu có
        context = {
            'request': request,
            'shop_id': shop_id
        }

        serializer = BulkUpdateOrderStatusSerializer(data=request.data, context=context)
        if serializer.is_valid():
            result = serializer.save()

            # Cập nhật sold_count nếu trạng thái là trạng thái hoàn thành
            new_status = result.get('status')
            completed_statuses = ['delivered', 'received', 'received_reviewed']

            if new_status in completed_statuses:
                order_ids = result.get('order_ids', [])
                order_items = OrderItem.objects.filter(order_id__in=order_ids)

                product_quantities = order_items.values('product').annotate(
                    total_quantity=Sum('quantity')
                )

                for pq in product_quantities:
                    Product.objects.filter(pk=pq['product']).update(
                        sold_count=F('sold_count') + pq['total_quantity']
                    )

                # Cập nhật trạng thái thanh toán thành công cho tất cả đơn hàng
                Order.objects.filter(
                    id__in=order_ids
                ).exclude(payment_status='success').update(payment_status='success')

            # Xử lý đơn hàng không cập nhật được
            original_order_ids = set(request.data.get('order_ids', []))
            updated_order_ids = set(result['order_ids'])
            not_updated_ids = original_order_ids - updated_order_ids

            message = f'Đã cập nhật trạng thái cho {result["count"]} đơn hàng'
            if not_updated_ids:
                message += f'. {len(not_updated_ids)} đơn hàng không được cập nhật do đã bị hủy hoặc không hợp lệ'

            return Response({
                'status': 'success',
                'message': message,
                'data': {
                    'count': result['count'],
                    'order_ids': result['order_ids'],
                    'not_updated_ids': list(not_updated_ids),
                    'new_status': result['status'],
                    'updated_at': result['updated_at']
                }
            }, status=status.HTTP_200_OK)

        return Response({
            'status': 'error',
            'message': 'Không thể cập nhật trạng thái đơn hàng',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

class OrderListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """Lấy danh sách đơn hàng của người dùng"""
        user = request.user

        # Lọc dựa trên tham số truy vấn
        status_filter = request.query_params.get('status')
        search_query = request.query_params.get('search')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        # Bắt đầu truy vấn
        orders = Order.objects.filter(user=user).order_by('-created_at')

        # Áp dụng bộ lọc
        if status_filter:
            orders = orders.filter(order_status=status_filter)

        if search_query:
            orders = orders.filter(
                Q(id__icontains=search_query) |
                Q(items__product__name__icontains=search_query)
            ).distinct()

        if start_date:
            orders = orders.filter(created_at__gte=start_date)

        if end_date:
            orders = orders.filter(created_at__lte=end_date)

        # Phân trang
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 10))

        start = (page - 1) * page_size
        end = start + page_size

        total_count = orders.count()
        orders = orders[start:end]

        serializer = OrderListSerializer(orders, many=True)

        return Response({
            'status': 'success',
            'message': 'Đã lấy danh sách đơn hàng thành công',
            'data': {
                'orders': serializer.data,
                'pagination': {
                    'total': total_count,
                    'page': page,
                    'page_size': page_size,
                    'total_pages': (total_count + page_size - 1) // page_size
                }
            }
        }, status=status.HTTP_200_OK)


class OrderDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, order_id):
        """Lấy chi tiết đơn hàng"""
        user = request.user

        # Kiểm tra quyền truy cập
        if user.role == 'customer':
            order = get_object_or_404(Order, id=order_id, user=user)
        elif user.role == 'shop_owner':
            # Người bán chỉ có thể xem đơn hàng có sản phẩm từ cửa hàng của họ
            order = get_object_or_404(Order, id=order_id, items__shop__owner=user)
        else:  # Admin có thể xem tất cả
            order = get_object_or_404(Order, id=order_id)

        # Tải trước các dữ liệu liên quan để tối ưu truy vấn
        order = Order.objects.prefetch_related(
            'items',
            'items__product',
            'items__product__images',
            'items__variant',
            'items__variant__attribute_values',
            'items__variant__attribute_values__attribute_value',
            'items__variant__attribute_values__attribute_value__attribute',
            'items__shop',
            'tracking_items',
            'tracking_items__created_by'
        ).select_related('user', 'address').get(id=order.id)

        serializer = OrderDetailSerializer(order)

        return Response({
            'status': 'success',
            'message': 'Đã lấy chi tiết đơn hàng thành công',
            'data': serializer.data
        }, status=status.HTTP_200_OK)


class CreateOrderView(APIView):
    permission_classes = [IsCustomer]

    def post(self, request):
        """Tạo đơn hàng mới từ giỏ hàng"""
        serializer = CreateOrderSerializer(
            data=request.data,
            context={'request': request}
        )

        if serializer.is_valid():
            order = serializer.save()

            # Trả về thông tin đơn hàng đã tạo
            order_serializer = OrderDetailSerializer(order)

            return Response({
                'status': 'success',
                'message': 'Đã tạo đơn hàng thành công',
                'data': order_serializer.data
            }, status=status.HTTP_201_CREATED)

        return Response({
            'status': 'error',
            'message': 'Không thể tạo đơn hàng',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class UpdateOrderStatusView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def put(self, request, order_id):
        """Cập nhật trạng thái đơn hàng"""
        user = request.user

        # Xác định đơn hàng
        if user.role == 'customer':
            order = get_object_or_404(Order, id=order_id, user=user)
            # Khách hàng chỉ có thể hủy đơn hàng
            if request.data.get('status') != 'cancelled':
                return Response({
                    'status': 'error',
                    'message': 'Bạn chỉ có thể hủy đơn hàng, không thể thay đổi trạng thái khác'
                }, status=status.HTTP_403_FORBIDDEN)
        elif user.role == 'shop_owner':
            # Người bán chỉ có thể cập nhật đơn hàng có sản phẩm từ cửa hàng của họ
            order = get_object_or_404(Order, id=order_id, items__shop__owner=user)
        else:  # Admin có thể cập nhật tất cả
            order = get_object_or_404(Order, id=order_id)

        serializer = UpdateOrderStatusSerializer(
            instance=order,
            data=request.data,
            context={'request': request}
        )

        if serializer.is_valid():
            updated_order = serializer.save()

            # Trả về thông tin đơn hàng đã cập nhật
            order_serializer = OrderDetailSerializer(updated_order)

            return Response({
                'status': 'success',
                'message': 'Đã cập nhật trạng thái đơn hàng thành công',
                'data': order_serializer.data
            }, status=status.HTTP_200_OK)

        return Response({
            'status': 'error',
            'message': 'Không thể cập nhật trạng thái đơn hàng',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class UpdateOrderItemStatusView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def put(self, request, item_id):
        user = request.user
        order_item = None

        # Xác định quyền người dùng
        if user.role == 'customer':
            # Khách hàng chỉ được phép hủy đơn hàng của mình
            order_item = get_object_or_404(OrderItem, id=item_id, order__user=user)
            if request.data.get('status') != 'cancelled':
                return Response({
                    'status': 'error',
                    'message': 'Bạn chỉ có thể hủy mục đơn hàng, không thể thay đổi trạng thái khác'
                }, status=status.HTTP_403_FORBIDDEN)

        elif user.role == 'shop_owner':
            # Người bán chỉ được cập nhật đơn từ cửa hàng của họ
            order_item = get_object_or_404(OrderItem, id=item_id, shop__owner=user)

        else:
            # Admin được cập nhật mọi đơn
            order_item = get_object_or_404(OrderItem, id=item_id)

        serializer = UpdateOrderItemStatusSerializer(
            instance=order_item,
            data=request.data,
            context={'request': request}
        )

        if serializer.is_valid():
            old_status = order_item.status
            new_status = request.data.get('status')

            updated_item = serializer.save()

            # Cập nhật sold_count của sản phẩm nếu cần
            completed_statuses = ['delivered', 'received', 'received_reviewed']

            if new_status in completed_statuses and old_status not in completed_statuses:
                Product.objects.filter(pk=order_item.product.pk).update(
                    sold_count=F('sold_count') + order_item.quantity
                )
                # Cập nhật trạng thái thanh toán thành công
                if updated_item.order.payment_status != 'success':
                    updated_item.order.payment_status = 'success'
                    updated_item.order.save(update_fields=['payment_status'])

            elif old_status in completed_statuses and new_status in ['cancelled', 'returned']:
                Product.objects.filter(pk=order_item.product.pk).update(
                    sold_count=F('sold_count') - order_item.quantity
                )

            order_serializer = OrderDetailSerializer(updated_item.order)
            return Response({
                'status': 'success',
                'message': 'Đã cập nhật trạng thái mục đơn hàng thành công',
                'data': order_serializer.data
            }, status=status.HTTP_200_OK)

        return Response({
            'status': 'error',
            'message': 'Không thể cập nhật trạng thái mục đơn hàng',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class SellerOrdersView(APIView):
    """API dành cho người bán để xem các đơn hàng của cửa hàng họ"""
    permission_classes = [IsShopOwner]

    def get(self, request):
        """Lấy danh sách đơn hàng cho người bán"""
        user = request.user

        # Lọc dựa trên tham số truy vấn
        status_filter = request.query_params.get('status')
        search_query = request.query_params.get('search')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        # Lấy tất cả đơn hàng có sản phẩm từ cửa hàng của người bán
        orders = Order.objects.filter(items__shop__owner=user).distinct().order_by('-created_at')

        # Áp dụng bộ lọc
        if status_filter:
            orders = orders.filter(items__status=status_filter)

        if search_query:
            orders = orders.filter(
                Q(id__icontains=search_query) |
                Q(user__email__icontains=search_query) |
                Q(user__full_name__icontains=search_query) |
                Q(items__product__name__icontains=search_query)
            ).distinct()

        if start_date:
            orders = orders.filter(created_at__gte=start_date)

        if end_date:
            orders = orders.filter(created_at__lte=end_date)

        # Phân trang
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 10))

        start = (page - 1) * page_size
        end = start + page_size

        total_count = orders.count()
        orders = orders[start:end]

        serializer = OrderListSerializer(orders, many=True)

        return Response({
            'status': 'success',
            'message': 'Đã lấy danh sách đơn hàng cho người bán thành công',
            'data': {
                'orders': serializer.data,
                'pagination': {
                    'total': total_count,
                    'page': page,
                    'page_size': page_size,
                    'total_pages': (total_count + page_size - 1) // page_size
                }
            }
        }, status=status.HTTP_200_OK)

# orders/views.py
class CheckOrderCancellableView(APIView):
    """API kiểm tra xem đơn hàng có thể hủy được không"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, order_id):
        """Kiểm tra khả năng hủy đơn hàng"""
        user = request.user

        # Tìm đơn hàng cần kiểm tra
        try:
            order = Order.objects.get(id=order_id)

            # Kiểm tra quyền truy cập
            if order.user != user and user.role not in ['admin']:
                return Response({
                    'status': 'error',
                    'message': 'Bạn không có quyền truy cập đơn hàng này'
                }, status=status.HTTP_403_FORBIDDEN)

            # Kiểm tra khả năng hủy
            cancellable_statuses = ['pending', 'confirmed']
            is_cancellable = order.order_status in cancellable_statuses

            # Nếu đơn hàng đang vận chuyển và sắp đến nơi, có thể không cho hủy
            # Đây chỉ là ví dụ logic nghiệp vụ, có thể điều chỉnh
            if order.order_status == 'shipping':
                shipping_days = (timezone.now().date() - order.updated_at.date()).days
                if shipping_days <= 1:  # Nếu mới đi ship dưới 1 ngày
                    is_cancellable = False

            # Trả về kết quả
            return Response({
                'status': 'success',
                'data': {
                    'order_id': order.id,
                    'current_status': order.order_status,
                    'status_display': order.get_order_status_display(),
                    'is_cancellable': is_cancellable,
                    'payment_status': order.payment_status,
                    'cancellation_policy': "Đơn hàng chỉ có thể hủy ở trạng thái 'Chờ xác nhận' hoặc 'Đã xác nhận'."
                }
            }, status=status.HTTP_200_OK)

        except Order.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'Không tìm thấy đơn hàng'
            }, status=status.HTTP_404_NOT_FOUND)

# orders/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.shortcuts import get_object_or_404
from .models import Order
from .serializers import CancelOrderSerializer


class CancelOrderView(APIView):
    """API cho phép người dùng hủy đơn hàng của họ"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, order_id):
        """Hủy đơn hàng dựa trên ID"""
        user = request.user

        # Tìm đơn hàng cần hủy
        order = get_object_or_404(Order, id=order_id)

        # Kiểm tra quyền truy cập
        if order.user != user and user.role not in ['admin']:
            return Response({
                'status': 'error',
                'message': 'Bạn không có quyền hủy đơn hàng này'
            }, status=status.HTTP_403_FORBIDDEN)

        # Tạo và xác thực serializer
        serializer = CancelOrderSerializer(
            instance=order,
            data=request.data,
            context={'request': request}
        )

        if serializer.is_valid():
            # Thực hiện hủy đơn hàng
            cancelled_order = serializer.save()

            # Gửi thông báo cho shop về việc đơn hàng đã bị hủy nếu cần
            # Có thể implement thêm logic notification ở đây

            # Trả về kết quả
            return Response({
                'status': 'success',
                'message': 'Đơn hàng đã được hủy thành công',
                'data': {
                    'order_id': cancelled_order.id,
                    'status': cancelled_order.order_status,
                    'cancelled_at': cancelled_order.updated_at
                }
            }, status=status.HTTP_200_OK)

        return Response({
            'status': 'error',
            'message': 'Không thể hủy đơn hàng',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


# orders/views.py
class ConfirmOrderReceivedView(APIView):
    """API cho phép khách hàng xác nhận đã nhận được hàng"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, order_id):
        try:
            # Lấy đơn hàng
            order = Order.objects.get(id=order_id)

            # Sử dụng serializer để xác thực và cập nhật
            serializer = ConfirmOrderReceivedSerializer(
                instance=order,
                data=request.data,
                context={'request': request}
            )

            if serializer.is_valid():
                order = serializer.save()
                # Trả về dữ liệu đơn hàng đã cập nhật
                return_serializer = OrderDetailSerializer(order)
                return Response(return_serializer.data)

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except Order.DoesNotExist:
            return Response(
                {"detail": "Không tìm thấy đơn hàng"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"detail": f"Đã xảy ra lỗi: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )