# reviews/views.py
from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Count, Avg
from django.shortcuts import get_object_or_404
from .models import Review, ReviewLike, OrderReview
from .serializers import ReviewSerializer, ReviewLikeSerializer, OrderReviewSerializer, OrderReviewDetailSerializer
from orders.models import Order, OrderItem
import cloudinary.uploader
import json


class IsOwnerOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.user == request.user


class ReviewViewSet(viewsets.ModelViewSet):
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    filter_backends = [filters.OrderingFilter, filters.SearchFilter]
    ordering_fields = ['created_at', 'rating']
    search_fields = ['comment']

    @action(detail=False, methods=['get'])
    def product_reviews(self, request):
        """
        Lấy danh sách đánh giá theo sản phẩm với nhiều tùy chọn lọc và sắp xếp
        """
        product_id = request.query_params.get('product_id')
        if not product_id:
            return Response({"detail": "product_id là bắt buộc"}, status=status.HTTP_400_BAD_REQUEST)

        # Lọc theo sản phẩm và chỉ lấy các đánh giá đã được phê duyệt
        queryset = OrderReview.objects.filter(product_id=product_id, status='approved')

        # Lọc theo rating
        rating_filter = request.query_params.get('rating')
        if rating_filter:
            try:
                rating_filter = int(rating_filter)
                if 1 <= rating_filter <= 5:
                    queryset = queryset.filter(rating=rating_filter)
            except ValueError:
                pass  # Bỏ qua nếu rating không phải số nguyên

        # Lọc theo có hình ảnh hay không
        has_images = request.query_params.get('has_images')
        if has_images and has_images.lower() == 'true':
            queryset = queryset.exclude(images__isnull=True).exclude(images='[]').exclude(images='null')

        # Lọc theo có comment hay không
        has_comment = request.query_params.get('has_comment')
        if has_comment and has_comment.lower() == 'true':
            queryset = queryset.exclude(comment__isnull=True).exclude(comment='')

        # Sắp xếp
        sort_by = request.query_params.get('sort_by', 'created_at')
        sort_order = request.query_params.get('sort_order', 'desc')

        valid_sort_fields = ['created_at', 'rating']
        if sort_by not in valid_sort_fields:
            sort_by = 'created_at'

        if sort_order.lower() == 'asc':
            queryset = queryset.order_by(sort_by)
        else:
            queryset = queryset.order_by(f'-{sort_by}')

        # Phân trang
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 10))

        # Đếm tổng số đánh giá trước khi phân trang
        total_count = queryset.count()

        # Tạo slice cho phân trang
        start = (page - 1) * page_size
        end = start + page_size

        # Thực hiện phân trang
        queryset = queryset[start:end]

        # Thêm thông tin về người dùng và số lượt thích
        serializer = self.get_serializer(queryset, many=True)

        # Tính số lượng đánh giá theo từng rating
        rating_counts = {
            1: Review.objects.filter(product_id=product_id, status='approved', rating=1).count(),
            2: Review.objects.filter(product_id=product_id, status='approved', rating=2).count(),
            3: Review.objects.filter(product_id=product_id, status='approved', rating=3).count(),
            4: Review.objects.filter(product_id=product_id, status='approved', rating=4).count(),
            5: Review.objects.filter(product_id=product_id, status='approved', rating=5).count(),
        }

        # Tính rating trung bình
        from django.db.models import Avg
        avg_rating = Review.objects.filter(
            product_id=product_id,
            status='approved'
        ).aggregate(Avg('rating'))['rating__avg'] or 0

        # Chuẩn bị dữ liệu phản hồi
        response_data = {
            'reviews': serializer.data,
            'pagination': {
                'total': total_count,
                'page': page,
                'page_size': page_size,
                'total_pages': (total_count + page_size - 1) // page_size
            },
            'summary': {
                'average_rating': round(avg_rating, 1),
                'total_reviews': total_count,
                'rating_distribution': rating_counts
            },
            'filters': {
                'product_id': product_id,
                'rating': rating_filter,
                'has_images': has_images,
                'has_comment': has_comment
            },
            'sorting': {
                'sort_by': sort_by,
                'sort_order': sort_order
            }
        }

        return Response(response_data)
    def get_queryset(self):
        queryset = Review.objects.filter(status='approved')
        product_id = self.request.query_params.get('product_id')

        if product_id:
            queryset = queryset.filter(product_id=product_id)

        return queryset

    @action(detail=False, methods=['get'])
    def reviewable_items(self, request):
        """Trả về danh sách các order items đã giao hàng và chưa được đánh giá"""
        # Lấy các order đã giao hàng thành công
        delivered_orders = Order.objects.filter(
            user=request.user,
            order_status='received'  # Changed from status to order_status
        )

        # Lấy các order items từ các order này
        order_items = OrderItem.objects.filter(
            order__in=delivered_orders
        ).exclude(
            # Loại trừ các đã được đánh giá
            review__user=request.user
        )

        # Serializer đơn giản cho order items
        data = [{
            'order_item_id': item.id,
            'order_id': item.order.id,
            'product_id': item.variant.product.id,
            'product_name': item.variant.product.name,
            'variant_sku': item.variant.sku,
            'product_image': item.variant.image_url,
            'date_delivered': item.order.updated_at
        } for item in order_items]

        return Response(data)

    @action(detail=True, methods=['post'])
    def like(self, request, pk=None):
        review = self.get_object()
        user = request.user

        # Kiểm tra người dùng đã like review này chưa
        like_exists = ReviewLike.objects.filter(review=review, user=user).exists()

        if like_exists:
            # Nếu đã like thì xóa like (unlike)
            ReviewLike.objects.filter(review=review, user=user).delete()
            return Response({"detail": "Review unliked successfully"}, status=status.HTTP_200_OK)
        else:
            # Nếu chưa like thì tạo like mới
            ReviewLike.objects.create(review=review, user=user)
            return Response({"detail": "Review liked successfully"}, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'])
    def my_reviews(self, request):
        """Trả về tất cả đánh giá của người dùng hiện tại"""
        reviews = Review.objects.filter(user=request.user)
        serializer = self.get_serializer(reviews, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def product_summary(self, request):
        """Trả về tóm tắt đánh giá cho một sản phẩm"""
        product_id = request.query_params.get('product_id')
        if not product_id:
            return Response({"detail": "Product ID is required"}, status=status.HTTP_400_BAD_REQUEST)

        reviews = Review.objects.filter(product_id=product_id, status='approved')

        # Tính số lượng đánh giá theo từng mức rating
        rating_counts = {
            1: reviews.filter(rating=1).count(),
            2: reviews.filter(rating=2).count(),
            3: reviews.filter(rating=3).count(),
            4: reviews.filter(rating=4).count(),
            5: reviews.filter(rating=5).count(),
        }

        # Tính rating trung bình
        avg_rating = reviews.aggregate(Avg('rating'))['rating__avg'] or 0

        return Response({
            'product_id': product_id,
            'average_rating': round(avg_rating, 1),
            'total_reviews': reviews.count(),
            'rating_distribution': rating_counts
        })

    @action(detail=False, methods=['get'])
    def reviewable_orders(self, request):
        """Trả về danh sách các đơn hàng đã nhận và chưa được đánh giá"""
        # Lấy các đơn hàng đã nhận thành công
        reviewable_orders = Order.objects.filter(
            user=request.user,
            order_status='received'
        ).exclude(
            # Loại trừ các đơn hàng đã được đánh giá
            reviews__user=request.user
        )

        # Tạo phản hồi đơn giản
        data = []
        for order in reviewable_orders:
            # Lấy thông tin sản phẩm đầu tiên làm đại diện
            first_item = order.items.first()
            product_image = None
            product_name = None

            if first_item:
                product = first_item.variant.product
                thumbnail = product.images.filter(is_thumbnail=True).first()
                if thumbnail:
                    product_image = thumbnail.image_url
                else:
                    first_image = product.images.first()
                    if first_image:
                        product_image = first_image.image_url

                product_name = product.name

            # Đếm số lượng sản phẩm trong đơn hàng
            product_count = order.items.count()

            # Thêm thông tin đơn hàng vào kết quả
            data.append({
                'order_id': order.id,
                'order_date': order.created_at,
                'received_date': order.updated_at,
                'total_amount': order.total_amount,
                'first_product_name': product_name,
                'first_product_image': product_image,
                'product_count': product_count
            })

        return Response(data)

    # reviews/views.py
    @action(detail=False, methods=['post'])
    def create_order_review(self, request):
        """Tạo đánh giá chung cho toàn bộ đơn hàng và cập nhật trạng thái"""
        order_id = request.data.get('order_id')
        rating = request.data.get('rating')
        comment = request.data.get('comment')

        if not order_id:
            return Response({"detail": "order_id là bắt buộc"}, status=status.HTTP_400_BAD_REQUEST)

        if not rating:
            return Response({"detail": "rating là bắt buộc"}, status=status.HTTP_400_BAD_REQUEST)

        # Kiểm tra rating hợp lệ
        try:
            rating = int(rating)
            if not 1 <= rating <= 5:
                return Response({"detail": "rating phải từ 1 đến 5"}, status=status.HTTP_400_BAD_REQUEST)
        except ValueError:
            return Response({"detail": "rating phải là số nguyên từ 1 đến 5"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            order = Order.objects.get(id=order_id)
        except Order.DoesNotExist:
            return Response({"detail": "Không tìm thấy đơn hàng"}, status=status.HTTP_404_NOT_FOUND)

        # Kiểm tra đơn hàng thuộc về người dùng hiện tại
        if order.user != request.user:
            return Response({"detail": "Bạn chỉ có thể đánh giá đơn hàng của mình"},
                            status=status.HTTP_403_FORBIDDEN)

        # Kiểm tra đơn hàng đã nhận hàng chưa
        if order.order_status != 'received':
            return Response({"detail": "Bạn chỉ có thể đánh giá đơn hàng đã nhận"},
                            status=status.HTTP_400_BAD_REQUEST)

        # Kiểm tra đã đánh giá đơn hàng này chưa
        if OrderReview.objects.filter(user=request.user, order=order).exists():
            return Response({"detail": "Bạn đã đánh giá đơn hàng này rồi"},
                            status=status.HTTP_400_BAD_REQUEST)

        # Sử dụng transaction để đảm bảo tính nhất quán của dữ liệu
        from django.db import transaction
        with transaction.atomic():
            # Xử lý upload ảnh lên Cloudinary
            uploaded_image_urls = []
            if 'images' in request.FILES:
                images = request.FILES.getlist('images')
                # Giới hạn tối đa 3 ảnh
                for image in images[:3]:
                    # Upload ảnh lên Cloudinary
                    upload_result = cloudinary.uploader.upload(
                        image,
                        folder=f"reviews/orders/{order.id}",
                    )
                    # Lấy URL ảnh đã upload
                    image_url = upload_result.get('secure_url')
                    uploaded_image_urls.append(image_url)

            # Tạo đánh giá đơn hàng mới
            order_review = OrderReview.objects.create(
                order=order,
                user=request.user,
                rating=rating,
                comment=comment,
                images=json.dumps(uploaded_image_urls) if uploaded_image_urls else None,
                status='approved'
            )

            # Từ điển để lưu trữ sản phẩm đã xử lý, tránh cập nhật trùng lặp
            processed_products = {}

            # LẤY DANH SÁCH ORDER ITEMS TỪ ORDER
            order_items = order.items.all()

            # Tạo đánh giá cho từng sản phẩm trong đơn hàng với cùng điểm đánh giá
            for item in order_items:
                # Kiểm tra xem sản phẩm này đã được đánh giá chưa
                if not Review.objects.filter(user=request.user, order_item=item).exists():
                    Review.objects.create(
                        order_item=item,
                        product=item.product,  # Sử dụng item.product thay vì item.variant.product
                        user=request.user,
                        rating=rating,
                        comment=comment,
                        images=json.dumps(uploaded_image_urls) if uploaded_image_urls else None,
                        status='approved'
                    )

                    # Thêm sản phẩm vào danh sách đã xử lý
                    product_id = item.product.id
                    processed_products[product_id] = item.product

            # Cập nhật rating trung bình cho từng sản phẩm
            from django.db.models import Avg
            for product_id, product in processed_products.items():
                # Tính rating trung bình từ tất cả đánh giá đã phê duyệt
                avg_rating = Review.objects.filter(
                    product_id=product_id,
                    status='approved'
                ).aggregate(Avg('rating'))['rating__avg'] or 0

                # Làm tròn 1 chữ số thập phân và cập nhật
                product.rating = round(avg_rating, 1)
                product.save(update_fields=['rating', 'updated_at'])

            # Cập nhật trạng thái đơn hàng thành "received_reviewed"
            order.order_status = 'received_reviewed'
            order.save(update_fields=['order_status', 'updated_at'])

            # Tạo bản ghi theo dõi đơn hàng mới
            from orders.models import OrderTracking
            OrderTracking.objects.create(
                order=order,
                status='received_reviewed',
                note="Khách hàng đã đánh giá đơn hàng",
                created_by=request.user
            )

            # Cập nhật các order item cùng lúc
            order.items.all().update(status='received_reviewed')

        serializer = OrderReviewSerializer(order_review)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'])
    def my_order_reviews(self, request):
        """Trả về tất cả đánh giá đơn hàng của người dùng hiện tại"""
        order_reviews = OrderReview.objects.filter(user=request.user)
        serializer = OrderReviewSerializer(order_reviews, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def create_from_order(self, request):
        """Tạo đánh giá cho sản phẩm từ đơn hàng đã giao"""
        order_item_id = request.data.get('order_item_id')
        rating = request.data.get('rating')
        comment = request.data.get('comment')

        if not order_item_id:
            return Response({"detail": "order_item_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        if not rating:
            return Response({"detail": "rating is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            order_item = OrderItem.objects.get(id=order_item_id)
        except OrderItem.DoesNotExist:
            return Response({"detail": "Order item not found"}, status=status.HTTP_404_NOT_FOUND)

        # Kiểm tra đơn hàng thuộc về người dùng hiện tại
        if order_item.order.user != request.user:
            return Response({"detail": "You can only review products from your own orders"},
                            status=status.HTTP_403_FORBIDDEN)

        # Kiểm tra đơn hàng đã giao hàng
        if order_item.order.order_status != 'received':
            return Response({"detail": "You can only review products from delivered orders"},
                            status=status.HTTP_400_BAD_REQUEST)

        # Kiểm tra đã đánh giá order_item này chưa
        if Review.objects.filter(user=request.user, order_item=order_item).exists():
            return Response({"detail": "You have already reviewed this order item"},
                            status=status.HTTP_400_BAD_REQUEST)

        # Xử lý upload ảnh lên Cloudinary
        uploaded_image_urls = []
        if 'images' in request.FILES:
            images = request.FILES.getlist('images')
            # Giới hạn tối đa 3 ảnh
            for image in images[:3]:
                # Upload ảnh lên Cloudinary
                upload_result = cloudinary.uploader.upload(
                    image,
                    folder=f"reviews/{order_item.variant.product.id}",
                )
                # Lấy URL ảnh đã upload
                image_url = upload_result.get('secure_url')
                uploaded_image_urls.append(image_url)

        # Tạo đánh giá mới
        review_data = {
            'order_item': order_item,
            'product': order_item.variant.product,
            'user': request.user,
            'rating': rating,
            'comment': comment,
            'images': uploaded_image_urls,  # Lưu danh sách URL dưới dạng list
            'status': 'approved'  # Đặt trạng thái là pending để chờ phê duyệt
        }

        review = Review.objects.create(**review_data)
        serializer = self.get_serializer(review)

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'])
    def order_reviews_by_product(self, request):
        """
        Lấy danh sách đánh giá đơn hàng theo sản phẩm
        """
        product_id = request.query_params.get('product_id')
        if not product_id:
            return Response({"detail": "product_id là bắt buộc"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Tìm đơn hàng có chứa sản phẩm này
        relevant_orders = Order.objects.filter(items__product_id=product_id).distinct()
        
        # Lấy các đánh giá cho các đơn hàng đó
        queryset = OrderReview.objects.filter(
            order__in=relevant_orders,
            status='approved'
        ).select_related('user', 'order').prefetch_related('order__items', 'order__items__product', 'order__items__product__images')
        
        # Lọc theo rating
        rating_filter = request.query_params.get('rating')
        if rating_filter:
            try:
                rating_filter = int(rating_filter)
                if 1 <= rating_filter <= 5:
                    queryset = queryset.filter(rating=rating_filter)
            except ValueError:
                pass  # Bỏ qua nếu rating không phải số nguyên
        
        # Lọc theo có hình ảnh hay không
        has_images = request.query_params.get('has_images')
        if has_images and has_images.lower() == 'true':
            queryset = queryset.exclude(images__isnull=True).exclude(images='[]').exclude(images='null')
        
        # Lọc theo có comment hay không
        has_comment = request.query_params.get('has_comment')
        if has_comment and has_comment.lower() == 'true':
            queryset = queryset.exclude(comment__isnull=True).exclude(comment='')
        
        # Sắp xếp
        sort_by = request.query_params.get('sort_by', 'created_at')
        sort_order = request.query_params.get('sort_order', 'desc')
        
        valid_sort_fields = ['created_at', 'rating']
        if sort_by not in valid_sort_fields:
            sort_by = 'created_at'
        
        if sort_order.lower() == 'asc':
            queryset = queryset.order_by(sort_by)
        else:
            queryset = queryset.order_by(f'-{sort_by}')
        
        # Tính số lượng đánh giá theo từng rating và rating trung bình
        from django.db.models import Avg, Count
        rating_stats = queryset.values('rating').annotate(count=Count('id'))
        
        rating_counts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        for stat in rating_stats:
            if 1 <= stat['rating'] <= 5:
                rating_counts[stat['rating']] = stat['count']
        
        # Tính rating trung bình
        avg_rating = queryset.aggregate(Avg('rating'))['rating__avg'] or 0
        
        # Phân trang
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 10))
        
        # Đếm tổng số đánh giá trước khi phân trang
        total_count = queryset.count()
        
        # Tạo slice cho phân trang
        start = (page - 1) * page_size
        end = start + page_size
        
        # Thực hiện phân trang
        queryset = queryset[start:end]
        
        # Serializer với context chứa product_id
        serializer_context = {'product_id': product_id}
        serializer = OrderReviewDetailSerializer(queryset, many=True, context=serializer_context)
        
        # Chuẩn bị dữ liệu phản hồi
        response_data = {
            'reviews': serializer.data,
            'pagination': {
                'total': total_count,
                'page': page,
                'page_size': page_size,
                'total_pages': (total_count + page_size - 1) // page_size
            },
            'summary': {
                'average_rating': round(avg_rating, 1),
                'total_reviews': total_count,
                'rating_distribution': rating_counts
            },
            'filters': {
                'product_id': product_id,
                'rating': rating_filter,
                'has_images': has_images,
                'has_comment': has_comment
            },
            'sorting': {
                'sort_by': sort_by,
                'sort_order': sort_order
            }
        }
        
        return Response(response_data)

    @action(detail=False, methods=['get'])
    def shop_reviews(self, request):
        """
        Lấy danh sách đánh giá theo shop với nhiều tùy chọn lọc và sắp xếp
        """
        shop_id = request.query_params.get('shop_id')
        if not shop_id:
            return Response({"detail": "shop_id là bắt buộc"}, status=status.HTTP_400_BAD_REQUEST)

        # Lọc theo shop và chỉ lấy các đánh giá đã được phê duyệt
        queryset = Review.objects.filter(
            product__shop_id=shop_id,
            status='approved'
        ).select_related('user', 'product')

        # Lọc theo rating
        rating_filter = request.query_params.get('rating')
        if rating_filter:
            try:
                rating_filter = int(rating_filter)
                if 1 <= rating_filter <= 5:
                    queryset = queryset.filter(rating=rating_filter)
            except ValueError:
                pass

        # Lọc theo có hình ảnh hay không
        has_images = request.query_params.get('has_images')
        if has_images and has_images.lower() == 'true':
            queryset = queryset.exclude(images__isnull=True).exclude(images='[]').exclude(images='null')

        # Lọc theo có comment hay không
        has_comment = request.query_params.get('has_comment')
        if has_comment and has_comment.lower() == 'true':
            queryset = queryset.exclude(comment__isnull=True).exclude(comment='')

        # Sắp xếp
        sort_by = request.query_params.get('sort_by', 'created_at')
        sort_order = request.query_params.get('sort_order', 'desc')

        valid_sort_fields = ['created_at', 'rating']
        if sort_by not in valid_sort_fields:
            sort_by = 'created_at'

        if sort_order.lower() == 'asc':
            queryset = queryset.order_by(sort_by)
        else:
            queryset = queryset.order_by(f'-{sort_by}')

        # Tính số lượng đánh giá theo từng rating
        rating_counts = {
            1: queryset.filter(rating=1).count(),
            2: queryset.filter(rating=2).count(),
            3: queryset.filter(rating=3).count(),
            4: queryset.filter(rating=4).count(),
            5: queryset.filter(rating=5).count(),
        }

        # Tính rating trung bình
        avg_rating = queryset.aggregate(Avg('rating'))['rating__avg'] or 0

        # Phân trang
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 10))

        # Đếm tổng số đánh giá trước khi phân trang
        total_count = queryset.count()

        # Tạo slice cho phân trang
        start = (page - 1) * page_size
        end = start + page_size

        # Thực hiện phân trang
        queryset = queryset[start:end]

        # Serialize dữ liệu
        serializer = self.get_serializer(queryset, many=True)

        # Chuẩn bị dữ liệu phản hồi
        response_data = {
            'reviews': serializer.data,
            'pagination': {
                'total': total_count,
                'page': page,
                'page_size': page_size,
                'total_pages': (total_count + page_size - 1) // page_size
            },
            'summary': {
                'average_rating': round(avg_rating, 1),
                'total_reviews': total_count,
                'rating_distribution': rating_counts
            },
            'filters': {
                'shop_id': shop_id,
                'rating': rating_filter,
                'has_images': has_images,
                'has_comment': has_comment
            },
            'sorting': {
                'sort_by': sort_by,
                'sort_order': sort_order
            }
        }

        return Response(response_data)