# cart/views.py
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from .models import Cart, CartItem
from products.models import ProductVariant
from .serializers import CartSerializer, AddToCartSerializer, UpdateCartItemSerializer


class CartView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Lấy giỏ hàng của người dùng hiện tại"""
        # Dùng prefetch_related và select_related để giảm số lượng truy vấn
        cart, created = Cart.objects.prefetch_related(
            'items',
            'items__variant',
            'items__variant__attribute_values',
            'items__variant__attribute_values__attribute_value',
            'items__variant__attribute_values__attribute_value__attribute',
            'items__variant__product',
            'items__variant__product__images',
            'items__variant__product__shop'
        ).get_or_create(user=request.user)
        
        serializer = CartSerializer(cart)
        
        return Response({
            'status': 'success',
            'message': 'Đã lấy giỏ hàng thành công',
            'data': serializer.data
        }, status=status.HTTP_200_OK)
    
    def post(self, request):
        """Thêm sản phẩm vào giỏ hàng"""
        serializer = AddToCartSerializer(data=request.data)

        if serializer.is_valid():
            variant_id = serializer.validated_data['variant_id']
            quantity = serializer.validated_data['quantity']

            # Lấy hoặc tạo giỏ hàng
            cart, created = Cart.objects.get_or_create(user=request.user)

            # Lấy biến thể sản phẩm
            variant = get_object_or_404(ProductVariant, id=variant_id)

            # Kiểm tra tồn kho
            if variant.stock < quantity:
                return Response({
                    'status': 'error',
                    'message': f'Số lượng yêu cầu vượt quá tồn kho. Chỉ còn {variant.stock} sản phẩm.'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Kiểm tra xem sản phẩm đã có trong giỏ hàng chưa
            cart_item, item_created = CartItem.objects.get_or_create(
                cart=cart,
                variant=variant,
                defaults={'quantity': quantity}
            )

            # Nếu sản phẩm đã có trong giỏ hàng thì cập nhật số lượng
            if not item_created:
                new_quantity = cart_item.quantity + quantity
                # Kiểm tra tồn kho một lần nữa
                if variant.stock < new_quantity:
                    return Response({
                        'status': 'error',
                        'message': f'Số lượng yêu cầu vượt quá tồn kho. Chỉ còn {variant.stock} sản phẩm.'
                    }, status=status.HTTP_400_BAD_REQUEST)

                cart_item.quantity = new_quantity
                cart_item.save()

            # Cập nhật thời gian cập nhật giỏ hàng
            cart.save()  # Tự động cập nhật updated_at

            # Trả về giỏ hàng đã cập nhật
            serializer = CartSerializer(cart)

            return Response({
                'status': 'success',
                'message': 'Đã thêm sản phẩm vào giỏ hàng thành công',
                'data': serializer.data
            }, status=status.HTTP_200_OK)

        return Response({
            'status': 'error',
            'message': 'Không thể thêm sản phẩm vào giỏ hàng',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        """Xóa toàn bộ giỏ hàng"""
        cart = Cart.objects.filter(user=request.user).first()

        if cart:
            # Xóa tất cả các mục trong giỏ hàng
            CartItem.objects.filter(cart=cart).delete()

            # Cập nhật thời gian cập nhật giỏ hàng
            cart.save()  # Tự động cập nhật updated_at

            return Response({
                'status': 'success',
                'message': 'Đã xóa toàn bộ giỏ hàng thành công'
            }, status=status.HTTP_200_OK)

        return Response({
            'status': 'error',
            'message': 'Không tìm thấy giỏ hàng'
        }, status=status.HTTP_404_NOT_FOUND)


class CartItemView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def put(self, request, item_id):
        """Cập nhật số lượng mục trong giỏ hàng"""
        # Tìm mục giỏ hàng
        cart_item = get_object_or_404(CartItem, id=item_id)
        
        # Kiểm tra quyền sở hữu
        if cart_item.cart.user != request.user:
            return Response({
                'status': 'error',
                'message': 'Bạn không có quyền cập nhật mục này'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Xác thực dữ liệu
        serializer = UpdateCartItemSerializer(data=request.data)
        
        if serializer.is_valid():
            quantity = serializer.validated_data['quantity']
            
            # Kiểm tra tồn kho
            if cart_item.variant.stock < quantity:
                return Response({
                    'status': 'error',
                    'message': f'Số lượng yêu cầu vượt quá tồn kho. Chỉ còn {cart_item.variant.stock} sản phẩm.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Cập nhật số lượng
            cart_item.quantity = quantity
            cart_item.save()
            
            # Cập nhật thời gian cập nhật giỏ hàng
            cart_item.cart.save()  # Tự động cập nhật updated_at
            
            # Trả về giỏ hàng đã cập nhật với dữ liệu đã được tối ưu
            cart = Cart.objects.prefetch_related(
                'items',
                'items__variant',
                'items__variant__attribute_values',
                'items__variant__attribute_values__attribute_value',
                'items__variant__attribute_values__attribute_value__attribute',
                'items__variant__product',
                'items__variant__product__images',
                'items__variant__product__shop'
            ).get(id=cart_item.cart.id)
            
            cart_serializer = CartSerializer(cart)
            
            return Response({
                'status': 'success',
                'message': 'Đã cập nhật mục giỏ hàng thành công',
                'data': cart_serializer.data
            }, status=status.HTTP_200_OK)
        
        return Response({
            'status': 'error',
            'message': 'Không thể cập nhật mục giỏ hàng',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, item_id):
        """Xóa mục khỏi giỏ hàng"""
        # Tìm mục giỏ hàng
        cart_item = get_object_or_404(CartItem, id=item_id)
        
        # Kiểm tra quyền sở hữu
        if cart_item.cart.user != request.user:
            return Response({
                'status': 'error',
                'message': 'Bạn không có quyền xóa mục này'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Lưu trữ ID cart để có thể truy vấn lại sau khi xóa
        cart_id = cart_item.cart.id
        
        # Xóa mục giỏ hàng
        cart_item.delete()
        
        # Truy vấn lại giỏ hàng đầy đủ
        cart = Cart.objects.prefetch_related(
            'items',
            'items__variant',
            'items__variant__attribute_values',
            'items__variant__attribute_values__attribute_value',
            'items__variant__attribute_values__attribute_value__attribute',
            'items__variant__product',
            'items__variant__product__images',
            'items__variant__product__shop'
        ).get(id=cart_id)
        
        # Cập nhật thời gian cập nhật giỏ hàng
        cart.save()  # Tự động cập nhật updated_at
        
        # Trả về giỏ hàng đã cập nhật
        cart_serializer = CartSerializer(cart)
        
        return Response({
            'status': 'success',
            'message': 'Đã xóa mục giỏ hàng thành công',
            'data': cart_serializer.data
        }, status=status.HTTP_200_OK)