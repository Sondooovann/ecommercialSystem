from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import UserRegistrationView, OTPVerificationView, ResendOTPView, LoginView, UserProfileView, \
    UserProfileUpdateView, ChangePasswordView, DeleteAccountView, ForgotPasswordRequestView, ResetPasswordView, \
    AdminBulkDeleteUsersView, AdminUserListCreateView, AdminUserStatisticsView, AdminUserStatusBulkUpdateView, \
    AdminUserDetailView, AdminResetUserPasswordView
from core.views import (
    AddressListCreateView,
    AddressDetailView,
    SetDefaultAddressView
)
from core.views import ProvinceListView, DistrictListView, WardListView

app_name = 'core'

urlpatterns = [
    # Public APIs
    path('register/', UserRegistrationView.as_view(), name='user-registration'),
    path('verify-otp/', OTPVerificationView.as_view(), name='otp-verification'),
    path('resend-otp/', ResendOTPView.as_view(), name='resend-otp'),

    path('login/', LoginView.as_view(), name='login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('forgot-password/', ForgotPasswordRequestView.as_view(), name='forgot-password'),
    path('reset-password/', ResetPasswordView.as_view(), name='reset-password'),

    # Protected APIs - Require Bearer token
    path('profile/', UserProfileView.as_view(), name='user-profile'),
    path('profile/update/', UserProfileUpdateView.as_view(), name='user-profile-update'),
    path('profile/change-password/', ChangePasswordView.as_view(), name='user-change-password'),
    path('profile/delete-account/', DeleteAccountView.as_view(), name='user-delete-account'),

    path('addresses/', AddressListCreateView.as_view(), name='address-list-create'),
    path('addresses/<int:pk>/', AddressDetailView.as_view(), name='address-detail'),
    path('addresses/<int:pk>/set-default/', SetDefaultAddressView.as_view(), name='address-set-default'),

    path('locations/provinces/', ProvinceListView.as_view(), name='province-list'),
    path('locations/districts/', DistrictListView.as_view(), name='district-list'),
    path('locations/wards/', WardListView.as_view(), name='ward-list'),
    path('admin/users/bulk-delete/', AdminBulkDeleteUsersView.as_view(), name='admin-user-bulk-delete'),

    path('admin/users/', AdminUserListCreateView.as_view(), name='admin-user-list'),
    path('admin/users/statistics/', AdminUserStatisticsView.as_view(), name='admin-user-statistics'),
    path('admin/users/bulk-update-status/', AdminUserStatusBulkUpdateView.as_view(),
         name='admin-user-bulk-update-status'),
    path('admin/users/<int:user_id>/', AdminUserDetailView.as_view(), name='admin-user-detail'),
    path('admin/users/<int:user_id>/reset-password/', AdminResetUserPasswordView.as_view(),
         name='admin-user-reset-password'),
]
