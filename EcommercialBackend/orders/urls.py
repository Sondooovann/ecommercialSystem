# orders/urls.py
from django.urls import path
from . import views
from .views import ConfirmOrderReceivedView, AdminOrderListView, AdminOrderDetailView, AdminUpdateOrderStatusView, \
    AdminUpdateOrderItemStatusView, AdminOrderAnalyticsView, AdminCreateOrderTrackingView, AdminBulkDeleteOrderView

urlpatterns = [
    # Đơn hàng của người dùng
    path('', views.OrderListView.as_view(), name='order-list'),
    path('create/', views.CreateOrderView.as_view(), name='create-order'),
    path('<int:order_id>/', views.OrderDetailView.as_view(), name='order-detail'),
    path('<int:order_id>/status/', views.UpdateOrderStatusView.as_view(), name='update-order-status'),
    path('items/<int:item_id>/status/', views.UpdateOrderItemStatusView.as_view(), name='update-order-item-status'),

    # API cho người bán
    path('seller/', views.SellerOrdersView.as_view(), name='seller-orders'),

    # API mới để cập nhật nhiều đơn hàng
    path('bulk-update-status/', views.BulkUpdateOrderStatusView.as_view(), name='bulk-update-order-status'),
    # API mới cho hủy đơn hàng
    path('<int:order_id>/cancel/', views.CancelOrderView.as_view(), name='cancel-order'),
    path('orders/<int:order_id>/confirm-received/', ConfirmOrderReceivedView.as_view(), name='confirm-order-received'),
    path('<int:order_id>/check-cancellable/', views.CheckOrderCancellableView.as_view(), name='check-cancellable'),

    #Admin
    path('admin/orders/', AdminOrderListView.as_view(), name='admin-orders-list'),
    path('admin/orders/<str:order_id>/', AdminOrderDetailView.as_view(), name='admin-order-detail'),
    path('admin/orders/<str:order_id>/status/', AdminUpdateOrderStatusView.as_view(), name='admin-update-order-status'),
    path('admin/order-items/<str:item_id>/status/', AdminUpdateOrderItemStatusView.as_view(),
         name='admin-update-order-item-status'),
    path('admin/orders/analytics/', AdminOrderAnalyticsView.as_view(), name='admin-order-analytics'),
    path('admin/orders/<str:order_id>/tracking/', AdminCreateOrderTrackingView.as_view(),
         name='admin-create-order-tracking'),
    path('admin/orders/bulk-delete/', AdminBulkDeleteOrderView.as_view(), name='admin-bulk-delete-orders'),

]
