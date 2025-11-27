from django.urls import path

from core.views import AdminUserListCreateView, AdminUserStatisticsView, AdminUserStatusBulkUpdateView, \
    AdminUserDetailView, AdminResetUserPasswordView
from . import views

from .views import CategoryProductsView, TopSellingProductsView

urlpatterns = [
    # QUẢN LÝ SẢN PHẨM CHO CHỦ CỬA HÀNG
    # GET: Lấy danh sách tất cả sản phẩm của cửa hàng (có phân trang, lọc, tìm kiếm)
    # POST: Tạo sản phẩm mới cho cửa hàng
    path('shops/<int:shop_id>/products/', views.ShopProductsView.as_view(), name='shop-products'),

    # GET: Lấy thông tin chi tiết của một sản phẩm
    # PUT: Cập nhật thông tin sản phẩm
    # DELETE: Xóa sản phẩm
    path('<int:product_id>/', views.ProductDetailView.as_view(), name='product-detail'),

    # QUẢN LÝ HÌNH ẢNH SẢN PHẨM
    # GET: Lấy tất cả hình ảnh của sản phẩm
    # POST: Thêm hình ảnh mới cho sản phẩm
    path('<int:product_id>/images/', views.ProductImageManagementView.as_view(), name='product-images'),

    # PUT: Cập nhật thông tin hình ảnh (như đặt làm ảnh đại diện, thay đổi thứ tự hiển thị)
    # DELETE: Xóa hình ảnh của sản phẩm
    path('<int:product_id>/images/<int:image_id>/', views.ProductImageManagementView.as_view(),
         name='product-image-detail'),

    # QUẢN LÝ BIẾN THỂ SẢN PHẨM (như kích thước, màu sắc...)
    # GET: Lấy tất cả biến thể của sản phẩm
    # POST: Thêm biến thể mới cho sản phẩm
    path('<int:product_id>/variants/', views.ProductVariantManagementView.as_view(), name='product-variants'),

    # PUT: Cập nhật thông tin biến thể (giá, tồn kho, thuộc tính...)
    # DELETE: Xóa biến thể của sản phẩm
    path('<int:product_id>/variants/<int:variant_id>/', views.ProductVariantManagementView.as_view(),
         name='product-variant-detail'),

    # THỐNG KÊ VÀ THAO TÁC HÀNG LOẠT
    # GET: Lấy thống kê sản phẩm của cửa hàng (số lượng sản phẩm theo trạng thái, danh mục...)
    path('shops/<int:shop_id>/products/stats/', views.ShopProductStatsView.as_view(), name='shop-product-stats'),

    # POST: Thực hiện hành động hàng loạt trên nhiều sản phẩm (kích hoạt, vô hiệu hóa, xóa...)
    path('shops/<int:shop_id>/products/bulk-action/', views.ProductBulkActionView.as_view(),
         name='product-bulk-action'),

    # APIs cho danh mục sản phẩm
    path('categories/', views.CategoryListView.as_view(), name='category-list'),
    path('categories/<int:category_id>/', views.CategoryDetailView.as_view(), name='category-detail'),
    path('categories/create/', views.CategoryDetailView.as_view(), name='category-create'),

    # API để lấy các sản phẩm nổi bật ngẫu nhiên
    path('featured-products/', views.FeaturedProductsView.as_view(), name='featured-products'),

    # URL pattern with category_id in the URL
    path('categories/<int:category_id>/products/', CategoryProductsView.as_view(), name='category-products'),

    path('products/by-category/', CategoryProductsView.as_view(), name='products-by-category'),

    path('top-selling/', TopSellingProductsView.as_view(), name='top-selling-products'),

    # Admin User Management URLs
]
