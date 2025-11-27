# shops/views.py
import cloudinary.uploader
from django.http import Http404
from rest_framework.parsers import MultiPartParser, FormParser
from datetime import datetime, timedelta
from core.permission import IsShopOwner, IsCustomer
from core.views import IsAdminUser
from .serializers import ShopCreateSerializer, AdminShopListSerializer, AdminShopDetailSerializer, \
    AdminShopUpdateSerializer, AdminShopSettingsUpdateSerializer
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from .models import Shop
from .serializers import ShopDetailSerializer, ShopListSerializer
from .models import ShopFollower
from .serializers import ShopFollowerSerializer, ShopSettingSerializer
from .models import ShopSetting
from .serializers import ShopSettingUpdateSerializer, ShopUpdateSerializer
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from core.models import User
from django.utils import timezone


from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum, Count

from shops.models import Shop, ShopFollower
from products.models import Product
from orders.models import Order, OrderItem
from core.models import User
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum, Count, F

from shops.models import Shop, ShopFollower
from products.models import Product
from orders.models import Order, OrderItem
from core.models import User


class MyShopStatisticsView(APIView):
    """API to get comprehensive statistics for the current user's shop"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get statistics for the authenticated user's shop including orders, products, followers, revenue, and customers"""
        # Check if the user has a shop
        try:
            shop = Shop.objects.get(owner=request.user)
        except Shop.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'You do not have a shop'
            }, status=status.HTTP_404_NOT_FOUND)

        # Get statistics
        # 1. Product count
        product_count = Product.objects.filter(shop=shop).count()

        # 2. Follower count
        follower_count = ShopFollower.objects.filter(shop=shop).count()

        # 3. Order count and Revenue
        # Get all order items for products from this shop
        order_items = OrderItem.objects.filter(variant__product__shop=shop)

        # For orders, count distinct orders that contain products from this shop
        order_count = Order.objects.filter(items__in=order_items).distinct().count()

        # Calculate total revenue - sum of (price_per_item * quantity) for all order items
        revenue = order_items.annotate(
            item_total=F('price') * F('quantity')  # Also fixed field name here if needed
        ).aggregate(total=Sum('item_total'))['total'] or 0

        # 4. Customer count (unique users who placed orders)
        customer_count = Order.objects.filter(
            items__in=order_items
        ).values('user').distinct().count()

        return Response({
            'status': 'success',
            'message': 'Shop statistics retrieved successfully',
            'data': {
                'shop_id': shop.id,
                'shop_name': shop.name,
                'order_count': order_count,
                'product_count': product_count,
                'follower_count': follower_count,
                'revenue': revenue,
                'customer_count': customer_count
            }
        }, status=status.HTTP_200_OK)

class ShopStatisticsView(APIView):
    """API to get comprehensive statistics for a shop"""
    permission_classes = [IsAuthenticated]

    def get(self, request, shop_id=None):
        """Get statistics for a shop including orders, products, followers, revenue, and customers"""
        # If shop_id is not provided, try to get from query parameters
        if not shop_id:
            shop_id = request.query_params.get('shop_id')

        if not shop_id:
            return Response({
                'status': 'error',
                'message': 'Shop ID is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Check if the shop exists
        try:
            shop = Shop.objects.get(id=shop_id)
        except Shop.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'Shop does not exist'
            }, status=status.HTTP_404_NOT_FOUND)

        # Check if user is the shop owner or staff
        if not (request.user.is_staff or request.user == shop.owner):
            return Response({
                'status': 'error',
                'message': 'You do not have permission to view shop statistics'
            }, status=status.HTTP_403_FORBIDDEN)

        # Get statistics
        # 1. Product count
        product_count = Product.objects.filter(shop=shop).count()

        # 2. Follower count
        follower_count = ShopFollower.objects.filter(shop=shop).count()

        # 3. Order count and Revenue
        # Get all order items for products from this shop
        order_items = OrderItem.objects.filter(product_variant__product__shop=shop)
        order_count = Order.objects.filter(orderitem__in=order_items).distinct().count()

        # Calculate total revenue
        revenue = order_items.aggregate(
            total_revenue=Sum('price_per_item') * Sum('quantity')
        ).get('total_revenue', 0)

        if revenue is None:
            revenue = 0

        # 4. Customer count (unique users who placed orders)
        customer_count = Order.objects.filter(
            orderitem__in=order_items
        ).values('user').distinct().count()

        return Response({
            'status': 'success',
            'message': 'Shop statistics retrieved successfully',
            'data': {
                'shop_id': shop.id,
                'shop_name': shop.name,
                'order_count': order_count,
                'product_count': product_count,
                'follower_count': follower_count,
                'revenue': revenue,
                'customer_count': customer_count
            }
        }, status=status.HTTP_200_OK)
class ShopCreateView(APIView):
    # Lớp quyền - Chỉ cho phép chủ cửa hàng truy cập
    permission_classes = [IsShopOwner]
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request):
        # Xử lý tải lên logo vào Cloudinary
        if 'logo' in request.FILES:
            logo_file = request.FILES['logo']
            upload_result = cloudinary.uploader.upload(
                logo_file,
                folder=f"shops/{request.user.id}/logos",
            )
            logo_url = upload_result.get('secure_url')
            request.data['logo'] = logo_url  # Gán lại vào data

        # Xử lý tải lên banner vào Cloudinary
        if 'banner' in request.FILES:
            banner_file = request.FILES['banner']
            upload_result = cloudinary.uploader.upload(
                banner_file,
                folder=f"shops/{request.user.id}/banners",
            )
            banner_url = upload_result.get('secure_url')
            request.data['banner'] = banner_url  # Gán lại vào data

        serializer = ShopCreateSerializer(data=request.data, context={'request': request})

        if serializer.is_valid():
            shop = serializer.save()

            return Response({
                'status': 'success',
                'message': 'Đã tạo cửa hàng thành công',
                'data': {
                    'id': shop.id,
                    'name': shop.name,
                    'status': shop.status,
                    'logo_url': shop.logo,
                    'banner_url': shop.banner,
                    'owner_id': shop.owner.id
                }
            }, status=status.HTTP_201_CREATED)

        return Response({
            'status': 'error',
            'message': 'Không thể tạo cửa hàng',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class ShopDetailView(APIView):
    # Lớp quyền - Cho phép tất cả người dùng truy cập
    permission_classes = [permissions.AllowAny]
    
    def get(self, request, shop_id):
        # Lấy thông tin chi tiết cửa hàng
        shop = get_object_or_404(Shop, id=shop_id)
        serializer = ShopDetailSerializer(shop)
        return Response({
            'status': 'success',
            'message': 'Đã lấy thông tin chi tiết cửa hàng',
            'data': serializer.data
        }, status=status.HTTP_200_OK)


class ShopListView(APIView):
    # Lớp quyền - Cho phép tất cả người dùng truy cập
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        # Lấy tham số truy vấn để lọc
        status_filter = request.query_params.get('status')
        owner_id = request.query_params.get('owner_id')
        search_query = request.query_params.get('search')
        
        # Bắt đầu với tất cả cửa hàng
        shops = Shop.objects.select_related('owner').all()
        
        # Áp dụng bộ lọc nếu được cung cấp
        if status_filter:
            shops = shops.filter(status=status_filter)
        
        if owner_id:
            shops = shops.filter(owner_id=owner_id)
        
        if search_query:
            shops = shops.filter(name__icontains=search_query)
        
        # Lấy tham số phân trang
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 10))
        
        # Phân trang thủ công (có thể sử dụng lớp phân trang DRF thay thế)
        start = (page - 1) * page_size
        end = start + page_size
        
        # Lấy tổng số để hiển thị thông tin phân trang
        total_count = shops.count()
        shops = shops[start:end]
        
        serializer = ShopListSerializer(shops, many=True)
        
        return Response({
            'status': 'success',
            'message': 'Đã lấy danh sách cửa hàng thành công',
            'data': {
                'shops': serializer.data,
                'pagination': {
                    'total': total_count,
                    'page': page,
                    'page_size': page_size,
                    'total_pages': (total_count + page_size - 1) // page_size
                }
            }
        }, status=status.HTTP_200_OK)


class UserShopsView(APIView):
    # Lớp quyền - Yêu cầu người dùng đã xác thực
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Lấy danh sách cửa hàng thuộc sở hữu của người dùng đã xác thực"""
        user = request.user
        shops = Shop.objects.filter(owner=user)
        if not shops.exists():
            return Response({
                'status': 'error',
                'code': '1002',
                'message': 'Bạn chưa sở hữu của hàng nào.',
                'data': []
            }, status=status.HTTP_404_NOT_FOUND)
        serializer = ShopListSerializer(shops, many=True)
        
        return Response({
            'status': 'success',
            'message': 'Đã lấy danh sách cửa hàng của bạn thành công',
            'data': serializer.data
        }, status=status.HTTP_200_OK)


class FollowShopView(APIView):
    # Lớp quyền - Yêu cầu người dùng đã xác thực và là customer
    permission_classes = [IsCustomer]
    
    def post(self, request, shop_id):
        """Theo dõi một cửa hàng"""
        user = request.user
        shop = get_object_or_404(Shop, id=shop_id)
        
        # Kiểm tra xem người dùng có phải là customer không
        if user.role != 'customer':
            return Response({
                'status': 'error',
                'message': 'Chỉ khách hàng mới có thể theo dõi cửa hàng'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Ngăn chủ cửa hàng theo dõi cửa hàng của chính họ
        if shop.owner == user:
            return Response({
                'status': 'error',
                'message': 'Bạn không thể theo dõi cửa hàng của chính mình'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Kiểm tra nếu đã theo dõi
        if ShopFollower.objects.filter(user=user, shop=shop).exists():
            return Response({
                'status': 'error',
                'message': 'Bạn đã theo dõi cửa hàng này rồi'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Tạo mối quan hệ người theo dõi
        follower = ShopFollower.objects.create(user=user, shop=shop)
        
        return Response({
            'status': 'success',
            'message': f'Bạn đã bắt đầu theo dõi {shop.name}',
            'data': ShopFollowerSerializer(follower).data
        }, status=status.HTTP_201_CREATED)
    
    def delete(self, request, shop_id):
        """Hủy theo dõi một cửa hàng"""
        user = request.user
        shop = get_object_or_404(Shop, id=shop_id)
        
        # Tìm và xóa mối quan hệ người theo dõi
        follower = ShopFollower.objects.filter(user=user, shop=shop).first()
        
        if not follower:
            return Response({
                'status': 'error',
                'message': 'Bạn chưa theo dõi cửa hàng này'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        follower.delete()
        
        return Response({
            'status': 'success',
            'message': f'Bạn đã ngừng theo dõi {shop.name}'
        }, status=status.HTTP_200_OK)


class ShopFollowersView(APIView):
    # Lớp quyền - Yêu cầu người dùng đã xác thực
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, shop_id):
        """Lấy tất cả người theo dõi của một cửa hàng"""
        shop = get_object_or_404(Shop, id=shop_id)
        
        # Kiểm tra xem người dùng có phải là chủ cửa hàng
        if shop.owner != request.user:
            return Response({
                'status': 'error',
                'message': 'Chỉ chủ cửa hàng mới có thể xem danh sách người theo dõi'
            }, status=status.HTTP_403_FORBIDDEN)
        
        followers = ShopFollower.objects.filter(shop=shop).select_related('user')
        
        # Kiểm tra nếu không có người theo dõi
        if not followers.exists():
            return Response({
                'status': 'success',
                'message': 'Cửa hàng chưa có người theo dõi nào',
                'data': {
                    'total_followers': 0,
                    'followers': []
                }
            }, status=status.HTTP_200_OK)
        
        serializer = ShopFollowerSerializer(followers, many=True)
        
        return Response({
            'status': 'success',
            'message': 'Đã lấy danh sách người theo dõi cửa hàng',
            'data': {
                'total_followers': followers.count(),
                'followers': serializer.data
            }
        }, status=status.HTTP_200_OK)


class ShopFollowersTotalView(APIView):
    # Lớp quyền - Yêu cầu người dùng đã xác thực
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, shop_id):
        """Lấy tất cả người theo dõi của một cửa hàng"""
        shop = get_object_or_404(Shop, id=shop_id)

        # Kiểm tra xem người dùng có phải là chủ cửa hàng
        if shop.owner != request.user:
            return Response({
                'status': 'error',
                'message': 'Chỉ chủ cửa hàng mới có thể xem danh sách người theo dõi'
            }, status=status.HTTP_403_FORBIDDEN)

        followers = ShopFollower.objects.filter(shop=shop).select_related('user')

        # Kiểm tra nếu không có người theo dõi
        if not followers.exists():
            return Response({
                'status': 'success',
                'message': 'Cửa hàng chưa có người theo dõi nào',
                'data': {
                    'total_followers': 0,
                }
            }, status=status.HTTP_200_OK)

        serializer = ShopFollowerSerializer(followers, many=True)

        return Response({
            'status': 'success',
            'message': 'Đã lấy danh sách người theo dõi cửa hàng',
            'data': {
                'total_followers': followers.count(),
            }
        }, status=status.HTTP_200_OK)

class UserFollowedShopsView(APIView):
    # Lớp quyền - Chỉ cho phép khách hàng truy cập
    permission_classes = [IsCustomer]
    
    def get(self, request):
        """Lấy tất cả cửa hàng mà người dùng hiện tại đang theo dõi"""
        user = request.user
        
        # Kiểm tra xem người dùng có vai trò 'customer' không
        if user.role != 'customer':
            return Response({
                'status': 'error',
                'message': 'Chức năng này chỉ dành cho khách hàng'
            }, status=status.HTTP_403_FORBIDDEN)
        
        followed_shops = ShopFollower.objects.filter(user=user).select_related('shop')
        
        if not followed_shops.exists():
            return Response({
                'status': 'error',
                'message': 'Bạn chưa theo dõi cửa hàng nào',
                'data': []
            }, status=status.HTTP_404_NOT_FOUND)
        
        shops = [follow.shop for follow in followed_shops]
        serializer = ShopListSerializer(shops, many=True)
        
        return Response({
            'status': 'success',
            'message': 'Đã lấy danh sách cửa hàng đang theo dõi',
            'data': serializer.data
        }, status=status.HTTP_200_OK)


class ShopSettingsView(APIView):
    # Lớp quyền - Yêu cầu người dùng đã xác thực
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, shop_id):
        """Lấy cài đặt cửa hàng"""
        shop = get_object_or_404(Shop, id=shop_id)
        
        # Đảm bảo người dùng là chủ cửa hàng
        if shop.owner != request.user:
            return Response({
                'status': 'error',
                'message': 'Chỉ chủ cửa hàng mới có thể truy cập cài đặt cửa hàng'
            }, status=status.HTTP_403_FORBIDDEN)
        
        settings = get_object_or_404(ShopSetting, shop=shop)
        serializer = ShopSettingSerializer(settings)
        
        return Response({
            'status': 'success',
            'message': 'Đã lấy cài đặt cửa hàng',
            'data': serializer.data
        }, status=status.HTTP_200_OK)
    
    def put(self, request, shop_id):
        """Cập nhật cài đặt cửa hàng"""
        shop = get_object_or_404(Shop, id=shop_id)
        
        # Đảm bảo người dùng là chủ cửa hàng
        if shop.owner != request.user:
            return Response({
                'status': 'error',
                'message': 'Chỉ chủ cửa hàng mới có thể cập nhật cài đặt cửa hàng'
            }, status=status.HTTP_403_FORBIDDEN)
        
        settings = get_object_or_404(ShopSetting, shop=shop)
        serializer = ShopSettingUpdateSerializer(settings, data=request.data)
        
        if serializer.is_valid():
            serializer.save()
            return Response({
                'status': 'success',
                'message': 'Đã cập nhật cài đặt cửa hàng thành công',
                'data': serializer.data
            }, status=status.HTTP_200_OK)
        
        return Response({
            'status': 'error',
            'message': 'Không thể cập nhật cài đặt cửa hàng',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class ShopManagementView(APIView):
    # Lớp quyền - Yêu cầu người dùng đã xác thực
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)

    def get(self, request, shop_id):
        """Lấy thông tin chi tiết cửa hàng để chỉnh sửa"""
        shop = get_object_or_404(Shop, id=shop_id)

        # Đảm bảo người dùng là chủ cửa hàng
        if shop.owner != request.user:
            return Response({
                'status': 'error',
                'message': 'Chỉ chủ cửa hàng mới có thể truy cập quản lý cửa hàng'
            }, status=status.HTTP_403_FORBIDDEN)

        serializer = ShopDetailSerializer(shop)

        return Response({
            'status': 'success',
            'message': 'Đã lấy thông tin chi tiết cửa hàng',
            'data': serializer.data
        }, status=status.HTTP_200_OK)

    def put(self, request, shop_id):
        """Cập nhật thông tin chi tiết cửa hàng"""
        shop = get_object_or_404(Shop, id=shop_id)

        # Đảm bảo người dùng là chủ cửa hàng
        if shop.owner != request.user:
            return Response({
                'status': 'error',
                'message': 'Chỉ chủ cửa hàng mới có thể cập nhật thông tin cửa hàng'
            }, status=status.HTTP_403_FORBIDDEN)

        serializer = ShopUpdateSerializer(shop, data=request.data)

        if serializer.is_valid():
            # Xử lý cập nhật logo
            if 'logo' in request.FILES:
                logo_file = request.FILES['logo']
                upload_result = cloudinary.uploader.upload(
                    logo_file,
                    folder=f"shops/{shop.owner.id}/logos",
                )
                shop.logo = upload_result.get('secure_url')

            # Xử lý cập nhật banner
            if 'banner' in request.FILES:
                banner_file = request.FILES['banner']
                upload_result = cloudinary.uploader.upload(
                    banner_file,
                    folder=f"shops/{shop.owner.id}/banners",
                )
                shop.banner = upload_result.get('secure_url')

            # Lưu dữ liệu đã xác thực
            shop = serializer.save()

            return Response({
                'status': 'success',
                'message': 'Đã cập nhật cửa hàng thành công',
                'data': ShopDetailSerializer(shop).data
            }, status=status.HTTP_200_OK)

        return Response({
            'status': 'error',
            'message': 'Không thể cập nhật cửa hàng',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, shop_id):
        """Xóa cửa hàng"""
        shop = get_object_or_404(Shop, id=shop_id)

        # Đảm bảo người dùng là chủ cửa hàng
        if shop.owner != request.user:
            return Response({
                'status': 'error',
                'message': 'Chỉ chủ cửa hàng mới có thể xóa cửa hàng'
            }, status=status.HTTP_403_FORBIDDEN)

        # Kiểm tra xem cửa hàng có sản phẩm hay không
        # Bạn có thể tùy chỉnh điều này dựa trên logic kinh doanh của bạn
        if shop.products.exists():
            return Response({
                'status': 'error',
                'message': 'Không thể xóa cửa hàng có sản phẩm. Vui lòng xóa tất cả sản phẩm trước.'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Lưu tên cửa hàng để trả về trong phản hồi
        shop_name = shop.name

        # Xóa cửa hàng
        shop.delete()

        return Response({
            'status': 'success',
            'message': f'Cửa hàng "{shop_name}" đã được xóa thành công'
        }, status=status.HTTP_200_OK)

# Thêm các view này

from .models import SizeChart
from .serializers import SizeChartSerializer

class SizeChartView(APIView):
    # Lớp quyền - Yêu cầu người dùng đã xác thực
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, shop_id):
        """Lấy tất cả biểu đồ kích thước cho một cửa hàng"""
        shop = get_object_or_404(Shop, id=shop_id)
        
        # Xác định xem người dùng có phải là chủ sở hữu (để có quyền chỉnh sửa)
        is_owner = shop.owner == request.user
        
        size_charts = SizeChart.objects.filter(shop=shop)
        serializer = SizeChartSerializer(size_charts, many=True)
        
        return Response({
            'status': 'success',
            'message': 'Đã lấy bảng kích thước',
            'data': {
                'size_charts': serializer.data,
                'is_owner': is_owner
            }
        }, status=status.HTTP_200_OK)
    
    def post(self, request, shop_id):
        """Tạo biểu đồ kích thước mới"""
        shop = get_object_or_404(Shop, id=shop_id)
        
        # Đảm bảo người dùng là chủ cửa hàng
        if shop.owner != request.user:
            return Response({
                'status': 'error',
                'message': 'Chỉ chủ cửa hàng mới có thể tạo bảng kích thước'
            }, status=status.HTTP_403_FORBIDDEN)
        
        serializer = SizeChartSerializer(data=request.data)
        
        if serializer.is_valid():
            serializer.save(shop=shop)
            
            return Response({
                'status': 'success',
                'message': 'Đã tạo bảng kích thước thành công',
                'data': serializer.data
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            'status': 'error',
            'message': 'Không thể tạo bảng kích thước',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class SizeChartDetailView(APIView):
    # Lớp quyền - Yêu cầu người dùng đã xác thực
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, chart_id):
        """Lấy một biểu đồ kích thước cụ thể"""
        size_chart = get_object_or_404(SizeChart, id=chart_id)
        
        # Bất kỳ ai cũng có thể xem biểu đồ kích thước
        serializer = SizeChartSerializer(size_chart)
        
        return Response({
            'status': 'success',
            'message': 'Đã lấy bảng kích thước',
            'data': serializer.data
        }, status=status.HTTP_200_OK)
    
    def put(self, request, chart_id):
        """Cập nhật biểu đồ kích thước"""
        size_chart = get_object_or_404(SizeChart, id=chart_id)
        
        # Đảm bảo người dùng là chủ cửa hàng
        if size_chart.shop.owner != request.user:
            return Response({
                'status': 'error',
                'message': 'Chỉ chủ cửa hàng mới có thể cập nhật bảng kích thước'
            }, status=status.HTTP_403_FORBIDDEN)
        
        serializer = SizeChartSerializer(size_chart, data=request.data)
        
        if serializer.is_valid():
            serializer.save()
            
            return Response({
                'status': 'success',
                'message': 'Đã cập nhật bảng kích thước thành công',
                'data': serializer.data
            }, status=status.HTTP_200_OK)
        
        return Response({
            'status': 'error',
            'message': 'Không thể cập nhật bảng kích thước',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, chart_id):
        """Xóa một biểu đồ kích thước"""
        size_chart = get_object_or_404(SizeChart, id=chart_id)
        
        # Đảm bảo người dùng là chủ cửa hàng
        if size_chart.shop.owner != request.user:
            return Response({
                'status': 'error',
                'message': 'Chỉ chủ cửa hàng mới có thể xóa bảng kích thước'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Lưu tên biểu đồ để trả về trong phản hồi
        chart_name = size_chart.name
        
        # Xóa biểu đồ
        size_chart.delete()
        
        return Response({
            'status': 'success',
            'message': f'Bảng kích thước "{chart_name}" đã được xóa thành công'
        }, status=status.HTTP_200_OK)

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .serializers import ShopFollowCheckSerializer
from .models import Shop

class CheckShopFollowView(APIView):
    """API endpoint to check if a user is following a shop"""

    def get(self, request, shop_id=None):
        # Handle case where shop_id is provided in URL
        if shop_id is None:
            shop_id = request.query_params.get('shop_id')

        if not shop_id:
            return Response({
                'status': 'error',
                'message': 'Shop ID is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Check if shop exists
        try:
            shop = Shop.objects.get(id=shop_id)
        except Shop.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'Shop not found'
            }, status=status.HTTP_404_NOT_FOUND)

        # Check if user is following the shop
        is_following = False
        if request.user.is_authenticated:
            is_following = ShopFollower.objects.filter(
                user=request.user,
                shop_id=shop_id
            ).exists()

        return Response({
            'status': 'success',
            'data': {
                'shop_id': shop_id,
                'is_following': is_following
            }
        }, status=status.HTTP_200_OK)


from django.db.models import Count, Q
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from .models import Shop
from .serializers import ShopListSerializer
from products.models import Product

class PopularShopsView(APIView):
    """API to get shops with high follower counts and many products"""
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        # Get query parameters for customization
        limit = int(request.query_params.get('limit', 10))
        min_followers = int(request.query_params.get('min_followers', 0))
        min_products = int(request.query_params.get('min_products', 0))

        # Start with all active shops
        shops = Shop.objects.filter(status='active')

        # Annotate shops with follower count and product count
        shops = shops.annotate(
            follower_count=Count('followers', distinct=True),
            product_count=Count('products', distinct=True, filter=Q(products__status='active'))
        )

        # Filter by minimum followers and products if specified
        if min_followers > 0:
            shops = shops.filter(follower_count__gte=min_followers)

        if min_products > 0:
            shops = shops.filter(product_count__gte=min_products)

        # Order by follower count (primary) and product count (secondary)
        shops = shops.order_by('-follower_count', '-product_count')

        # Apply limit
        shops = shops[:limit]

        # Prepare response
        serializer = ShopListSerializer(shops, many=True)

        # Include the counts in the response
        shop_data = []
        for i, shop in enumerate(shops):
            data = serializer.data[i]
            data['follower_count'] = shop.follower_count
            data['product_count'] = shop.product_count
            shop_data.append(data)

        return Response({
            'status': 'success',
            'message': 'Đã lấy danh sách cửa hàng phổ biến thành công',
            'data': {
                'shops': shop_data,
                'count': len(shop_data)
            }
        }, status=status.HTTP_200_OK)


class AdminShopListView(APIView):
    """View for admin to list and filter all shops"""
    permission_classes = [IsAdminUser]

    def get(self, request):
        """Get list of all shops with filtering options"""
        shops = Shop.objects.all().select_related('owner', 'settings')

        # Filtering options
        status = request.query_params.get('status')
        owner_id = request.query_params.get('owner_id')
        search = request.query_params.get('search')
        min_rating = request.query_params.get('min_rating')
        order_by = request.query_params.get('order_by', '-created_at')

        if status:
            shops = shops.filter(status=status)

        if owner_id:
            shops = shops.filter(owner_id=owner_id)

        if search:
            shops = shops.filter(
                models.Q(name__icontains=search) |
                models.Q(description__icontains=search) |
                models.Q(owner__email__icontains=search) |
                models.Q(owner__full_name__icontains=search)
            )

        if min_rating:
            shops = shops.filter(rating__gte=float(min_rating))

        # Order by specified field
        valid_order_fields = ['created_at', '-created_at', 'name', '-name',
                              'rating', '-rating', 'updated_at', '-updated_at']
        if order_by in valid_order_fields:
            shops = shops.order_by(order_by)
        else:
            shops = shops.order_by('-created_at')

        # Pagination
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 10))

        paginator = Paginator(shops, page_size)
        try:
            shops_page = paginator.page(page)
        except (PageNotAnInteger, EmptyPage):
            shops_page = paginator.page(1)

        serializer = AdminShopListSerializer(shops_page, many=True)

        return Response({
            'status': 'success',
            'message': 'Danh sách cửa hàng được lấy thành công',
            'data': {
                'shops': serializer.data,
                'pagination': {
                    'total': paginator.count,
                    'pages': paginator.num_pages,
                    'current_page': page,
                    'page_size': page_size
                }
            }
        })


class AdminShopDetailView(APIView):
    """View for admin to retrieve, update, or delete shop details"""
    permission_classes = [IsAdminUser]

    def get_object(self, shop_id):
        try:
            return Shop.objects.get(pk=shop_id)
        except Shop.DoesNotExist:
            raise Http404

    def get(self, request, shop_id):
        """Get detailed information about a shop"""
        shop = self.get_object(shop_id)
        serializer = AdminShopDetailSerializer(shop)

        return Response({
            'status': 'success',
            'message': 'Thông tin chi tiết cửa hàng được lấy thành công',
            'data': serializer.data
        })

    def put(self, request, shop_id):
        """Update shop details"""
        shop = self.get_object(shop_id)
        serializer = AdminShopUpdateSerializer(shop, data=request.data, partial=True)

        if serializer.is_valid():
            updated_shop = serializer.save()

            return Response({
                'status': 'success',
                'message': 'Cập nhật thông tin cửa hàng thành công',
                'data': AdminShopDetailSerializer(updated_shop).data
            })

        return Response({
            'status': 'error',
            'message': 'Không thể cập nhật cửa hàng',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, shop_id):
        """Delete a shop"""
        shop = self.get_object(shop_id)
        shop_name = shop.name

        # Delete the shop
        shop.delete()

        return Response({
            'status': 'success',
            'message': f'Cửa hàng "{shop_name}" đã được xóa thành công'
        })


class AdminShopSettingsView(APIView):
    """View for admin to update shop settings"""
    permission_classes = [IsAdminUser]

    def put(self, request, shop_id):
        """Update shop settings"""
        try:
            shop = Shop.objects.get(pk=shop_id)
        except Shop.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'Cửa hàng không tồn tại'
            }, status=status.HTTP_404_NOT_FOUND)

        try:
            shop_settings = ShopSetting.objects.get(shop=shop)
        except ShopSetting.DoesNotExist:
            # Create settings if they don't exist
            shop_settings = ShopSetting.objects.create(shop=shop)

        serializer = AdminShopSettingsUpdateSerializer(shop_settings, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()

            return Response({
                'status': 'success',
                'message': 'Cài đặt cửa hàng đã được cập nhật thành công',
                'data': serializer.data
            })

        return Response({
            'status': 'error',
            'message': 'Không thể cập nhật cài đặt cửa hàng',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class AdminShopStatusBulkUpdateView(APIView):
    """View for admin to update multiple shops' status at once"""
    permission_classes = [IsAdminUser]

    def post(self, request):
        """Update status for multiple shops"""
        shop_ids = request.data.get('shop_ids', [])
        new_status = request.data.get('status')

        if not shop_ids or not new_status:
            return Response({
                'status': 'error',
                'message': 'Thiếu thông tin bắt buộc',
                'errors': {
                    'shop_ids': 'Danh sách ID cửa hàng là bắt buộc',
                    'status': 'Trạng thái mới là bắt buộc'
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        # Validate status
        valid_statuses = ['active', 'inactive', 'banned', 'pending']
        if new_status not in valid_statuses:
            return Response({
                'status': 'error',
                'message': 'Trạng thái không hợp lệ',
                'errors': {
                    'status': f'Trạng thái phải là một trong {valid_statuses}'
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        # Update shops status
        updated_count = Shop.objects.filter(id__in=shop_ids).update(status=new_status)

        return Response({
            'status': 'success',
            'message': f'Đã cập nhật trạng thái của {updated_count} cửa hàng thành {new_status}',
            'data': {
                'updated_count': updated_count
            }
        })


class AdminShopBulkDeleteView(APIView):
    """View for admin to delete multiple shops at once"""
    permission_classes = [IsAdminUser]

    def post(self, request):
        """Delete multiple shops"""
        shop_ids = request.data.get('shop_ids', [])
        admin_password = request.data.get('password')

        if not shop_ids:
            return Response({
                'status': 'error',
                'message': 'Thiếu thông tin bắt buộc',
                'errors': {
                    'shop_ids': 'Danh sách ID cửa hàng là bắt buộc'
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        if not admin_password:
            return Response({
                'status': 'error',
                'message': 'Thiếu thông tin bắt buộc',
                'errors': {
                    'password': 'Mật khẩu xác nhận là bắt buộc'
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        # Verify admin's password
        if not request.user.check_password(admin_password):
            return Response({
                'status': 'error',
                'message': 'Mật khẩu không chính xác',
                'errors': {
                    'password': 'Mật khẩu xác nhận không đúng'
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        # Get shops to delete
        shops_to_delete = Shop.objects.filter(id__in=shop_ids)
        shop_count = shops_to_delete.count()

        if shop_count == 0:
            return Response({
                'status': 'error',
                'message': 'Không tìm thấy cửa hàng nào để xóa'
            }, status=status.HTTP_404_NOT_FOUND)

        # Get shop names for response
        shop_names = list(shops_to_delete.values_list('name', flat=True))

        # Delete shops
        deleted_count, _ = shops_to_delete.delete()

        return Response({
            'status': 'success',
            'message': f'Đã xóa {deleted_count} cửa hàng thành công',
            'data': {
                'deleted_count': deleted_count,
                'deleted_shops': shop_names
            }
        })


class AdminShopStatisticsView(APIView):
    """View for admin to get shop statistics"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get overall shop statistics"""
        # Total shops count
        total_shops = Shop.objects.count()

        # Shops by status
        shops_by_status = {
            'active': Shop.objects.filter(status='active').count(),
            'inactive': Shop.objects.filter(status='inactive').count(),
            'banned': Shop.objects.filter(status='banned').count(),
            'pending': Shop.objects.filter(status='pending').count()
        }

        # New shops in the last 7 days
        seven_days_ago = timezone.now() - timezone.timedelta(days=7)
        new_shops_last_7_days = Shop.objects.filter(created_at__gte=seven_days_ago).count()

        # New shops in the last 30 days
        thirty_days_ago = timezone.now() - timezone.timedelta(days=30)
        new_shops_last_30_days = Shop.objects.filter(created_at__gte=thirty_days_ago).count()

        # Top shops by follower count
        top_shops_by_followers = Shop.objects.annotate(
            follower_count=Count('followers')
        ).order_by('-follower_count')[:5]

        top_shops_data = []
        for shop in top_shops_by_followers:
            top_shops_data.append({
                'id': shop.id,
                'name': shop.name,
                'follower_count': shop.follower_count,
                'status': shop.status
            })

        # Top shops by product count
        top_shops_by_products = Shop.objects.annotate(
            product_count=Count('products')
        ).order_by('-product_count')[:5]

        top_product_shops_data = []
        for shop in top_shops_by_products:
            top_product_shops_data.append({
                'id': shop.id,
                'name': shop.name,
                'product_count': shop.product_count,
                'status': shop.status
            })

        return Response({
            'status': 'success',
            'message': 'Thống kê cửa hàng được lấy thành công',
            'data': {
                'total_shops': total_shops,
                'shops_by_status': shops_by_status,
                'new_shops_last_7_days': new_shops_last_7_days,
                'new_shops_last_30_days': new_shops_last_30_days,
                'top_shops_by_followers': top_shops_data,
                'top_shops_by_products': top_product_shops_data
            }
        })


class AdminFeatureShopView(APIView):
    """View for admin to feature or unfeature shops"""
    permission_classes = [IsAdminUser]

    def post(self, request, shop_id):
        """Feature or unfeature a shop"""
        try:
            shop = Shop.objects.get(pk=shop_id)
        except Shop.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'Cửa hàng không tồn tại'
            }, status=status.HTTP_404_NOT_FOUND)

        # Toggle the featured status
        featured = request.data.get('featured', False)

        # Assuming you have a 'featured' field in your Shop model
        # If not, you'll need to add it or use a different approach
        shop.featured = featured
        shop.save()

        action = "đánh dấu" if featured else "bỏ đánh dấu"

        return Response({
            'status': 'success',
            'message': f'Cửa hàng đã được {action} là nổi bật',
            'data': {
                'id': shop.id,
                'name': shop.name,
                'featured': featured
            }
        })


class AdminShopOwnerUpdateView(APIView):
    """View for admin to change the owner of a shop"""
    permission_classes = [IsAdminUser]

    def put(self, request, shop_id):
        """Change the owner of a shop"""
        try:
            shop = Shop.objects.get(pk=shop_id)
        except Shop.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'Cửa hàng không tồn tại'
            }, status=status.HTTP_404_NOT_FOUND)

        new_owner_id = request.data.get('owner_id')
        if not new_owner_id:
            return Response({
                'status': 'error',
                'message': 'ID người dùng mới là bắt buộc',
                'errors': {
                    'owner_id': 'Trường này là bắt buộc'
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            new_owner = User.objects.get(pk=new_owner_id)
        except User.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'Người dùng không tồn tại',
                'errors': {
                    'owner_id': 'Người dùng với ID này không tồn tại'
                }
            }, status=status.HTTP_404_NOT_FOUND)

        # Check if new owner has the right role
        if new_owner.role != 'shop_owner':
            return Response({
                'status': 'error',
                'message': 'Người dùng phải có vai trò là chủ cửa hàng',
                'errors': {
                    'owner_id': f'Người dùng có vai trò {new_owner.role}, phải là shop_owner'
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        # Check if new owner is active
        if new_owner.status != 'active':
            return Response({
                'status': 'error',
                'message': 'Người dùng phải có trạng thái hoạt động',
                'errors': {
                    'owner_id': f'Người dùng có trạng thái {new_owner.status}, phải là active'
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        # Store old owner for response
        old_owner = {
            'id': shop.owner.id,
            'email': shop.owner.email,
            'full_name': shop.owner.full_name
        }

        # Update the shop owner
        shop.owner = new_owner
        shop.save()

        return Response({
            'status': 'success',
            'message': 'Đã thay đổi chủ sở hữu cửa hàng thành công',
            'data': {
                'shop_id': shop.id,
                'shop_name': shop.name,
                'old_owner': old_owner,
                'new_owner': {
                    'id': new_owner.id,
                    'email': new_owner.email,
                    'full_name': new_owner.full_name
                }
            }
        })

# shops/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum, Count, F, Q
from django.db.models.functions import TruncDate
from datetime import datetime, timedelta
from .models import Shop
from orders.models import Order, OrderItem
from products.models import Product

class ShopAnalyticsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Get shop owned by current user
        try:
            shop = Shop.objects.get(owner=request.user)
        except Shop.DoesNotExist:
            return Response({"detail": "You don't have a shop."}, status=status.HTTP_404_NOT_FOUND)

        # Parse date parameters
        start_date_str = request.query_params.get('startDate', None)
        end_date_str = request.query_params.get('endDate', None)

        try:
            if start_date_str:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            else:
                start_date = (datetime.now() - timedelta(days=30)).date()

            if end_date_str:
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            else:
                end_date = datetime.now().date()
        except ValueError:
            return Response(
                {"detail": "Invalid date format. Use YYYY-MM-DD."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Calculate previous period for growth metrics
        days_diff = (end_date - start_date).days
        prev_end_date = start_date - timedelta(days=1)
        prev_start_date = prev_end_date - timedelta(days=days_diff)

        # Filter orders for the shop in the date range
        current_orders = Order.objects.filter(
            items__product__shop=shop,
            created_at__date__gte=start_date,
            created_at__date__lte=end_date
        ).distinct()

        # Filter orders for the previous period
        previous_orders = Order.objects.filter(
            items__product__shop=shop,
            created_at__date__gte=prev_start_date,
            created_at__date__lte=prev_end_date
        ).distinct()

        # Get total revenue
        current_revenue = current_orders.aggregate(
            total_revenue=Sum(F('items__price') * F('items__quantity'),
                              filter=Q(items__product__shop=shop))
        )['total_revenue'] or 0

        previous_revenue = previous_orders.aggregate(
            total_revenue=Sum(F('items__price') * F('items__quantity'),
                              filter=Q(items__product__shop=shop))
        )['total_revenue'] or 0

        # Count total orders
        total_orders = current_orders.count()
        previous_total_orders = previous_orders.count()

        # Count total products
        total_products = Product.objects.filter(shop=shop).count()
        previous_total_products = Product.objects.filter(
            shop=shop,
            created_at__date__lt=start_date
        ).count()

        # Count unique customers
        total_customers = current_orders.values('user').distinct().count()
        previous_total_customers = previous_orders.values('user').distinct().count()

        # Calculate growth percentages
        revenue_growth = calculate_growth(current_revenue, previous_revenue)
        orders_growth = calculate_growth(total_orders, previous_total_orders)
        products_growth = calculate_growth(total_products, previous_total_products)
        customers_growth = calculate_growth(total_customers, previous_total_customers)

        # Get daily sales data
        sales_data = current_orders.annotate(
            date=TruncDate('created_at')
        ).values('date').annotate(
            revenue=Sum(F('items__price') * F('items__quantity'),
                        filter=Q(items__product__shop=shop)),
            orders=Count('id', distinct=True)
        ).order_by('date')

        # Format sales data
        formatted_sales_data = []
        for entry in sales_data:
            formatted_sales_data.append({
                'date': entry['date'].strftime('%Y-%m-%d'),
                'revenue': float(entry['revenue'] or 0),
                'orders': entry['orders']
            })

        # Get top performing products
        product_performance = OrderItem.objects.filter(
            order__in=current_orders,
            product__shop=shop
        ).values(
            'product__name'
        ).annotate(
            revenue=Sum(F('price') * F('quantity')),
            units=Sum('quantity')
        ).order_by('-revenue')[:5]

        # Format product performance data
        formatted_product_performance = []
        for product in product_performance:
            formatted_product_performance.append({
                'name': product['product__name'],
                'revenue': float(product['revenue'] or 0),
                'units': product['units']
            })

        # Get customer segments - by purchase frequency
        customer_orders = current_orders.values('user').annotate(
            order_count=Count('id')
        )

        # Define segments
        new_customers = customer_orders.filter(order_count=1).count()
        returning_customers = customer_orders.filter(order_count__gt=1).count()

        customer_segments = [
            {'name': 'New Customers', 'value': new_customers},
            {'name': 'Returning Customers', 'value': returning_customers}
        ]

        # Get order status distribution
        order_status = current_orders.values('order_status').annotate(
            count=Count('id')
        ).order_by('order_status')

        formatted_order_status = []
        for status in order_status:
            formatted_order_status.append({
                'status': status['order_status'],
                'count': status['count']
            })

        # Prepare response
        analytics_data = {
            'overview': {
                'totalRevenue': float(current_revenue),
                'totalOrders': total_orders,
                'totalProducts': total_products,
                'totalCustomers': total_customers,
                'revenueGrowth': revenue_growth,
                'ordersGrowth': orders_growth,
                'productsGrowth': products_growth,
                'customersGrowth': customers_growth
            },
            'salesData': formatted_sales_data,
            'productPerformance': formatted_product_performance,
            'customerSegments': customer_segments,
            'orderStatus': formatted_order_status
        }

        return Response(analytics_data)

def calculate_growth(current, previous):
    """Calculate percentage growth from previous to current period"""
    if previous == 0:
        return 100 if current > 0 else 0
    return round(((current - previous) / previous) * 100, 2)

# shops/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum, Count, F, Q
from django.db.models.functions import TruncDate, TruncWeek, TruncMonth
from datetime import datetime, timedelta
from .models import Shop
from orders.models import Order

class ShopRevenueAnalyticsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Get shop owned by current user
        try:
            shop = Shop.objects.get(owner=request.user)
        except Shop.DoesNotExist:
            return Response({"detail": "You don't have a shop."}, status=status.HTTP_404_NOT_FOUND)

        # Parse date parameters
        start_date_str = request.query_params.get('startDate', None)
        end_date_str = request.query_params.get('endDate', None)
        interval_type = request.query_params.get('type', 'daily').lower()

        # Validate interval type
        if interval_type not in ['daily', 'weekly', 'monthly']:
            return Response(
                {"detail": "Invalid type. Use 'daily', 'weekly', or 'monthly'."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            if start_date_str:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            else:
                # Default to last 30 days for daily, 12 weeks for weekly, 12 months for monthly
                if interval_type == 'daily':
                    start_date = (datetime.now() - timedelta(days=30)).date()
                elif interval_type == 'weekly':
                    start_date = (datetime.now() - timedelta(weeks=12)).date()
                else:  # monthly
                    start_date = (datetime.now() - timedelta(days=365)).date()

            if end_date_str:
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            else:
                end_date = datetime.now().date()
        except ValueError:
            return Response(
                {"detail": "Invalid date format. Use YYYY-MM-DD."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Filter orders for the shop in the date range
        orders = Order.objects.filter(
            items__product__shop=shop,
            created_at__date__gte=start_date,
            created_at__date__lte=end_date
        ).distinct()

        # Set the appropriate truncation function based on interval type
        if interval_type == 'daily':
            trunc_func = TruncDate
            date_format = '%Y-%m-%d'
        elif interval_type == 'weekly':
            trunc_func = TruncWeek
            date_format = '%Y-%m-%d'  # Will use the first day of the week
        else:  # monthly
            trunc_func = TruncMonth
            date_format = '%Y-%m'

        # Get sales data aggregated by the selected interval
        sales_data = orders.annotate(
            date=trunc_func('created_at')
        ).values('date').annotate(
            revenue=Sum(F('items__price') * F('items__quantity'),
                        filter=Q(items__product__shop=shop)),
            orders=Count('id', distinct=True)
        ).order_by('date')

        # Format sales data
        formatted_sales_data = []
        for entry in sales_data:
            formatted_sales_data.append({
                'date': entry['date'].strftime(date_format),
                'revenue': float(entry['revenue'] or 0),
                'orders': entry['orders']
            })

        # Handle empty results
        if not formatted_sales_data:
            # Generate empty data points for the entire date range
            current_date = start_date
            while current_date <= end_date:
                if interval_type == 'daily':
                    formatted_sales_data.append({
                        'date': current_date.strftime(date_format),
                        'revenue': 0,
                        'orders': 0
                    })
                    current_date += timedelta(days=1)
                elif interval_type == 'weekly':
                    formatted_sales_data.append({
                        'date': current_date.strftime(date_format),
                        'revenue': 0,
                        'orders': 0
                    })
                    current_date += timedelta(days=7)
                else:  # monthly
                    formatted_sales_data.append({
                        'date': current_date.strftime(date_format),
                        'revenue': 0,
                        'orders': 0
                    })
                    # Move to first day of next month
                    if current_date.month == 12:
                        current_date = datetime.date(current_date.year + 1, 1, 1)
                    else:
                        current_date = datetime.date(current_date.year, current_date.month + 1, 1)

        # Prepare response
        response_data = {
            'salesData': formatted_sales_data
        }

        return Response(response_data)


# shops/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum, F, Q, Count, IntegerField, FloatField
from django.db.models.functions import Coalesce

from .models import Shop
from products.models import Product
from orders.models import OrderItem


class ShopProductAnalyticsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Get shop owned by current user
        try:
            shop = Shop.objects.get(owner=request.user)
        except Shop.DoesNotExist:
            return Response({"detail": "You don't have a shop."}, status=status.HTTP_404_NOT_FOUND)

        # Parse date parameters
        start_date_str = request.query_params.get('startDate', None)
        end_date_str = request.query_params.get('endDate', None)
        sort_by = request.query_params.get('sortBy', 'revenue').lower()

        # Validate sort_by parameter
        if sort_by not in ['revenue', 'units', 'views']:
            return Response(
                {"detail": "Invalid sortBy parameter. Use 'revenue', 'units', or 'views'."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            if start_date_str:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            else:
                # Default to last 30 days
                start_date = (datetime.now() - timedelta(days=30)).date()

            if end_date_str:
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            else:
                end_date = datetime.now().date()
        except ValueError:
            return Response(
                {"detail": "Invalid date format. Use YYYY-MM-DD."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get shop products
        products = Product.objects.filter(shop=shop)

        # Find orders in date range
        order_items = OrderItem.objects.filter(
            product__shop=shop,
            order__created_at__date__gte=start_date,
            order__created_at__date__lte=end_date
        )

        # Create a base queryset with all products
        products_data = products.annotate(
            # Calculate revenue using Coalesce to handle None values
            revenue=Coalesce(
                Sum(
                    F('order_items__price') * F('order_items__quantity'),
                    filter=Q(
                        order_items__order__created_at__date__gte=start_date,
                        order_items__order__created_at__date__lte=end_date
                    )
                ),
                0,
                output_field=FloatField()
            ),
            # Calculate units sold
            units=Coalesce(
                Sum(
                    'order_items__quantity',
                    filter=Q(
                        order_items__order__created_at__date__gte=start_date,
                        order_items__order__created_at__date__lte=end_date
                    )
                ),
                0,
                output_field=IntegerField()
            ),
            # Sum available stock across all variants
            stock=Coalesce(
                Sum('variants__stock'),
                0,
                output_field=IntegerField()
            ),
            # Get product views (if view tracking is implemented)
            views=Coalesce(
                Count(
                    'analytics__id',
                    filter=Q(
                        analytics__created_at__date__gte=start_date,
                        analytics__created_at__date__lte=end_date
                    )
                ),
                0,
                output_field=IntegerField()
            )
        )

        # Determine sort order
        if sort_by == 'revenue':
            products_data = products_data.order_by('-revenue')
        elif sort_by == 'units':
            products_data = products_data.order_by('-units')
        else:  # views
            products_data = products_data.order_by('-views')

        # Format product data
        formatted_products = []
        for product in products_data:
            formatted_products.append({
                'id': product.id,
                'name': product.name,
                'revenue': float(product.revenue),
                'units': product.units,
                'stock': product.stock,
                'price': float(product.price)
            })

        # Prepare response
        response_data = {
            'products': formatted_products
        }

        return Response(response_data)


class ShopCustomerAnalyticsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Get shop owned by current user
        try:
            shop = Shop.objects.get(owner=request.user)
        except Shop.DoesNotExist:
            return Response({"detail": "You don't have a shop."}, status=status.HTTP_404_NOT_FOUND)

        # Parse date parameters
        start_date_str = request.query_params.get('startDate', None)
        end_date_str = request.query_params.get('endDate', None)

        try:
            if start_date_str:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            else:
                # Default to last 30 days
                start_date = (datetime.now() - timedelta(days=30)).date()

            if end_date_str:
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            else:
                end_date = datetime.now().date()
        except ValueError:
            return Response(
                {"detail": "Invalid date format. Use YYYY-MM-DD."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get customers who have ordered from this shop in the date range
        customers = User.objects.filter(
            orders__items__product__shop=shop,
            orders__created_at__date__gte=start_date,
            orders__created_at__date__lte=end_date
        ).distinct()

        # Calculate customer segments based on total spent
        customer_segments = [
            {"name": "New", "value": 0},
            {"name": "Returning", "value": 0},
            {"name": "Loyal", "value": 0},
            {"name": "VIP", "value": 0}
        ]

        # Age distribution
        age_distribution = [
            {"age": "18-24", "value": 0},
            {"age": "25-34", "value": 0},
            {"age": "35-44", "value": 0},
            {"age": "45-54", "value": 0},
            {"age": "55+", "value": 0},
            {"age": "Unknown", "value": 0}
        ]

        # Top customers data
        top_customers = []

        for customer in customers:
            # Calculate total orders and spending for this customer at this shop
            orders = Order.objects.filter(
                user=customer,
                items__product__shop=shop,
                created_at__date__gte=start_date,
                created_at__date__lte=end_date
            ).distinct()

            order_count = orders.count()

            # Calculate total spent by this customer
            total_spent = OrderItem.objects.filter(
                order__user=customer,
                product__shop=shop,
                order__created_at__date__gte=start_date,
                order__created_at__date__lte=end_date
            ).aggregate(
                total=Sum(F('price') * F('quantity'), output_field=FloatField())
            )['total'] or 0

            # Determine customer segment
            if order_count == 1:
                customer_segments[0]["value"] += 1  # New
                status = "New"
            elif order_count < 4:
                customer_segments[1]["value"] += 1  # Returning
                status = "Returning"
            elif order_count < 10:
                customer_segments[2]["value"] += 1  # Loyal
                status = "Loyal"
            else:
                customer_segments[3]["value"] += 1  # VIP
                status = "VIP"

            # Calculate age group if birth_date is available
            if hasattr(customer, 'birth_date') and customer.birth_date:
                age = (datetime.date.today() - customer.birth_date).days // 365
                if age < 25:
                    age_distribution[0]["value"] += 1
                elif age < 35:
                    age_distribution[1]["value"] += 1
                elif age < 45:
                    age_distribution[2]["value"] += 1
                elif age < 55:
                    age_distribution[3]["value"] += 1
                else:
                    age_distribution[4]["value"] += 1
            else:
                age_distribution[5]["value"] += 1  # Unknown age

            # Add to top customers if they've spent enough
            if len(top_customers) < 10 or total_spent > top_customers[-1]["totalSpent"]:
                customer_data = {
                    "id": str(customer.id),
                    "name": f"{customer.full_name}".strip() or customer.username,
                    "email": customer.email,
                    "avatar": customer.profile_image.url if hasattr(customer, 'profile_image') and customer.profile_image else "",
                    "orders": order_count,
                    "totalSpent": float(total_spent),
                    "averageOrder": float(total_spent / order_count) if order_count > 0 else 0,
                    "status": status
                }

                top_customers.append(customer_data)
                # Sort by total spent and limit to top 10
                top_customers = sorted(top_customers, key=lambda x: x["totalSpent"], reverse=True)[:10]

        response_data = {
            "customerSegments": customer_segments,
            "ageDistribution": age_distribution,
            "topCustomers": top_customers
        }

        return Response(response_data)

from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework.response import Response
import pandas as pd
import io
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from datetime import datetime, timedelta

class ShopAnalyticsExportView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Get shop owned by current user
        try:
            shop = Shop.objects.get(owner=request.user)
        except Shop.DoesNotExist:
            return Response({"detail": "You don't have a shop."}, status=status.HTTP_404_NOT_FOUND)

        # Parse date parameters
        start_date_str = request.query_params.get('startDate', None)
        end_date_str = request.query_params.get('endDate', None)
        export_type = request.query_params.get('type', 'excel').lower()

        # Validate export type
        if export_type not in ['pdf', 'excel']:
            return Response(
                {"detail": "Invalid export type. Use 'pdf' or 'excel'."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            if start_date_str:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            else:
                # Default to last 30 days
                start_date = (datetime.now() - timedelta(days=30)).date()

            if end_date_str:
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            else:
                end_date = datetime.now().date()
        except ValueError:
            return Response(
                {"detail": "Invalid date format. Use YYYY-MM-DD."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get analytics data
        analytics_data = self.get_analytics_data(shop, start_date, end_date)

        # Generate the appropriate file
        if export_type == 'pdf':
            return self.generate_pdf(analytics_data, shop, start_date, end_date)
        else:
            return self.generate_excel(analytics_data, shop, start_date, end_date)

    def get_analytics_data(self, shop, start_date, end_date):
        """Collect all analytics data"""
        # Orders data
        orders = Order.objects.filter(
            items__product__shop=shop,
            created_at__date__gte=start_date,
            created_at__date__lte=end_date
        ).distinct()

        total_orders = orders.count()

        # Revenue data
        revenue = OrderItem.objects.filter(
            product__shop=shop,
            order__created_at__date__gte=start_date,
            order__created_at__date__lte=end_date
        ).aggregate(
            total=Sum(F('price') * F('quantity'), output_field=FloatField())
        )['total'] or 0

        # Calculate average order value
        avg_order_value = revenue / total_orders if total_orders > 0 else 0

        # Get top products
        top_products = OrderItem.objects.filter(
            product__shop=shop,
            order__created_at__date__gte=start_date,
            order__created_at__date__lte=end_date
        ).values('product__id', 'product__name').annotate(
            total_quantity=Sum('quantity'),
            total_revenue=Sum(F('price') * F('quantity'), output_field=FloatField())
        ).order_by('-total_revenue')[:10]

        # Get customer count
        customer_count = User.objects.filter(
            orders__items__product__shop=shop,
            orders__created_at__date__gte=start_date,
            orders__created_at__date__lte=end_date
        ).distinct().count()

        return {
            'shop_name': shop.name,
            'period': f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}",
            'total_orders': total_orders,
            'total_revenue': float(revenue),
            'avg_order_value': float(avg_order_value),
            'customer_count': customer_count,
            'top_products': list(top_products)
        }

    def generate_excel(self, data, shop, start_date, end_date):
        """Generate Excel file with analytics data"""
        buffer = io.BytesIO()

        # Create a Pandas Excel writer using XlsxWriter as the engine
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            # Summary sheet
            summary_data = {
                'Metric': ['Shop Name', 'Period', 'Total Orders', 'Total Revenue',
                           'Average Order Value', 'Total Customers'],
                'Value': [
                    data['shop_name'],
                    data['period'],
                    data['total_orders'],
                    f"${data['total_revenue']:.2f}",
                    f"${data['avg_order_value']:.2f}",
                    data['customer_count']
                ]
            }
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name='Summary', index=False)

            # Top Products sheet
            if data['top_products']:
                products_data = []
                for i, product in enumerate(data['top_products'], 1):
                    products_data.append({
                        'Rank': i,
                        'Product ID': product['product__id'],
                        'Product Name': product['product__name'],
                        'Units Sold': product['total_quantity'],
                        'Revenue': f"${product['total_revenue']:.2f}"
                    })
                products_df = pd.DataFrame(products_data)
                products_df.to_excel(writer, sheet_name='Top Products', index=False)

            # Format the workbook
            workbook = writer.book
            worksheet = writer.sheets['Summary']
            header_format = workbook.add_format({'bold': True, 'bg_color': '#DDDDDD'})

            # Apply header formatting
            for col_num, value in enumerate(summary_df.columns.values):
                worksheet.write(0, col_num, value, header_format)

            # Adjust column widths
            worksheet.set_column('A:A', 20)
            worksheet.set_column('B:B', 30)

        # Rewind the buffer and create response
        buffer.seek(0)

        # Create response
        response = HttpResponse(
            buffer.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="{shop.name}_analytics_{start_date}_{end_date}.xlsx"'

        return response

    def generate_pdf(self, data, shop, start_date, end_date):
        """Generate PDF with analytics data"""
        buffer = io.BytesIO()

        # Create the PDF object, using the BytesIO object as its "file"
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = []

        # Styles
        styles = getSampleStyleSheet()
        title_style = styles['Heading1']
        subtitle_style = styles['Heading2']

        # Add title
        elements.append(Paragraph(f"{data['shop_name']} - Analytics Report", title_style))
        elements.append(Paragraph(f"Period: {data['period']}", subtitle_style))

        # Summary table data
        summary_data = [
            ['Metric', 'Value'],
            ['Total Orders', str(data['total_orders'])],
            ['Total Revenue', f"${data['total_revenue']:.2f}"],
            ['Average Order Value', f"${data['avg_order_value']:.2f}"],
            ['Total Customers', str(data['customer_count'])],
        ]

        # Create summary table
        summary_table = Table(summary_data)
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (1, 0), 12),
            ('BACKGROUND', (0, 1), (1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))

        elements.append(summary_table)
        elements.append(Paragraph("Top Products", subtitle_style))

        # Top products table
        if data['top_products']:
            product_data = [['Rank', 'Product Name', 'Units Sold', 'Revenue']]
            for i, product in enumerate(data['top_products'], 1):
                product_data.append([
                    str(i),
                    product['product__name'],
                    str(product['total_quantity']),
                    f"${product['total_revenue']:.2f}"
                ])

            product_table = Table(product_data)
            product_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            elements.append(product_table)

        # Build the PDF
        doc.build(elements)

        # Get the value from the BytesIO buffer and create response
        pdf_data = buffer.getvalue()
        buffer.close()

        # Create response
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{shop.name}_analytics_{start_date}_{end_date}.pdf"'
        response.write(pdf_data)

        return response