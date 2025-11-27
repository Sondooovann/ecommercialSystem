from django.urls import path
from . import views
from .views import CheckShopFollowView, AdminShopListView, AdminShopStatisticsView, AdminShopStatusBulkUpdateView, \
    AdminShopBulkDeleteView, AdminShopDetailView, AdminShopSettingsView, AdminFeatureShopView, AdminShopOwnerUpdateView, \
    MyShopStatisticsView, ShopAnalyticsView, ShopRevenueAnalyticsView, ShopProductAnalyticsView, \
    ShopCustomerAnalyticsView, ShopAnalyticsExportView
from .views import PopularShopsView

urlpatterns = [
    # Add these to your existing URLs
    path('create/', views.ShopCreateView.as_view(), name='shop-create'),
    path('<int:shop_id>/', views.ShopDetailView.as_view(), name='shop-detail'),
    path('list/', views.ShopListView.as_view(), name='shop-list'),
    path('my-shops/', views.UserShopsView.as_view(), name='user-shops'),
    path('shops/popular/', PopularShopsView.as_view(), name='popular-shops'),

    path('<int:shop_id>/follow/', views.FollowShopView.as_view(), name='shop-follow'),
    path('<int:shop_id>/followers/', views.ShopFollowersView.as_view(), name='shop-followers'),
    path('<int:shop_id>/followers-total/', views.ShopFollowersTotalView.as_view(), name='shop-follow-total'),
    path('followed-shops/', views.UserFollowedShopsView.as_view(), name='followed-shops'),
    path('shops/<int:shop_id>/check-follow/', CheckShopFollowView.as_view(), name='check-shop-follow'),
    path('shops/check-follow/', CheckShopFollowView.as_view(), name='check-shop-follow-query'),

    path('<int:shop_id>/settings/', views.ShopSettingsView.as_view(), name='shop-settings'),
    path('<int:shop_id>/manage/', views.ShopManagementView.as_view(), name='shop-manage'),
    path('<int:shop_id>/size-charts/', views.SizeChartView.as_view(), name='shop-size-charts'),
    path('size-charts/<int:chart_id>/', views.SizeChartDetailView.as_view(), name='size-chart-detail'),

    # Admin Shop Management URLs
    path('admin/shops/', AdminShopListView.as_view(), name='admin-shop-list'),
    path('admin/shops/statistics/', AdminShopStatisticsView.as_view(), name='admin-shop-statistics'),
    path('admin/shops/bulk-update-status/', AdminShopStatusBulkUpdateView.as_view(),
         name='admin-shop-bulk-update-status'),
    path('admin/shops/bulk-delete/', AdminShopBulkDeleteView.as_view(), name='admin-shop-bulk-delete'),
    path('admin/shops/<int:shop_id>/', AdminShopDetailView.as_view(), name='admin-shop-detail'),
    path('admin/shops/<int:shop_id>/settings/', AdminShopSettingsView.as_view(), name='admin-shop-settings'),
    path('admin/shops/<int:shop_id>/feature/', AdminFeatureShopView.as_view(), name='admin-shop-feature'),
    path('admin/shops/<int:shop_id>/change-owner/', AdminShopOwnerUpdateView.as_view(), name='admin-shop-change-owner'),
    path('api/shops/my-statistics/', MyShopStatisticsView.as_view(), name='my-shop-statistics'),

    path('api/shops/<int:shop_id>/statistics/', AdminShopStatisticsView.as_view(), name='shop-statistics'),
    path('api/shops/statistics/', AdminShopStatisticsView.as_view(), name='shop-statistics-query'),
    path('api/shops/analytics/', ShopAnalyticsView.as_view(), name='shop-analytics'),
    path('api/shops/analytics/revenue/', ShopRevenueAnalyticsView.as_view(), name='shop-revenue-analytics'),
    path('api/shops/analytics/products/', ShopProductAnalyticsView.as_view(), name='shop-products-analytics'),
    path('api/shops/analytics/customers/', ShopCustomerAnalyticsView.as_view(), name='shop-customers-analytics'),
    path('analytics/export/', ShopAnalyticsExportView.as_view(), name='shop-analytics-export'),

]
