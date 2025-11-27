# cart/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Giỏ hàng
    # GET: Lấy giỏ hàng của người dùng
    # POST: Thêm sản phẩm vào giỏ hàng
    # DELETE: Xóa toàn bộ giỏ hàng
    path('', views.CartView.as_view(), name='cart'),

    # Mục giỏ hàng
    # PUT: Cập nhật số lượng mục trong giỏ hàng
    # DELETE: Xóa mục khỏi giỏ hàng
    path('items/<int:item_id>/', views.CartItemView.as_view(), name='cart-item'),
]