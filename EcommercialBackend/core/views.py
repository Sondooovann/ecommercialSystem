from django.http import Http404
from rest_framework import status, permissions
from rest_framework.views import APIView
from django.contrib.auth import get_user_model
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .models import OTP
from .serializers import UserRegistrationSerializer, OTPVerificationSerializer, LoginSerializer, \
    DeleteAccountSerializer, ChangePasswordSerializer, UserUpdateSerializer, ResetPasswordSerializer, \
    ForgotPasswordRequestSerializer, AdminResetUserPasswordSerializer, AdminUserDetailSerializer, \
    AdminUserUpdateSerializer, AdminUserCreateSerializer, AdminUserListSerializer
from .otp_manager import OTPManager
from core.responses.utils import send_otp_email, send_password_reset_email
from core.responses.response import APIResponse
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from core.models import Address, Province, District, Ward
from core.serializers import AddressSerializer, ProvinceSerializer, DistrictSerializer, WardSerializer
from django.utils import timezone

User = get_user_model()


# core/views.py
class ProvinceListView(APIView):
    """Lấy danh sách các tỉnh/thành phố"""
    permission_classes = [AllowAny]
    def get(self, request):
        provinces = Province.objects.all()
        serializer = ProvinceSerializer(provinces, many=True)

        return Response({
            'status': 'success',
            'message': 'Danh sách tỉnh/thành phố được lấy thành công',
            'data': {
                'provinces': serializer.data
            }
        })


class DistrictListView(APIView):
    """Lấy danh sách các quận/huyện theo tỉnh/thành phố"""
    permission_classes = [AllowAny]
    def get(self, request):
        province_id = request.query_params.get('province_id')

        if not province_id:
            return Response({
                'status': 'error',
                'message': 'Thiếu tham số province_id'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            districts = District.objects.filter(province_id=province_id)
            serializer = DistrictSerializer(districts, many=True)

            return Response({
                'status': 'success',
                'message': 'Danh sách quận/huyện được lấy thành công',
                'data': {
                    'districts': serializer.data
                }
            })
        except:
            return Response({
                'status': 'error',
                'message': 'Tỉnh/thành phố không tồn tại'
            }, status=status.HTTP_404_NOT_FOUND)


class WardListView(APIView):
    """Lấy danh sách các phường/xã theo quận/huyện"""
    permission_classes = [AllowAny]
    def get(self, request):
        district_id = request.query_params.get('district_id')

        if not district_id:
            return Response({
                'status': 'error',
                'message': 'Thiếu tham số district_id'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            wards = Ward.objects.filter(district_id=district_id)
            serializer = WardSerializer(wards, many=True)

            return Response({
                'status': 'success',
                'message': 'Danh sách phường/xã được lấy thành công',
                'data': {
                    'wards': serializer.data
                }
            })
        except:
            return Response({
                'status': 'error',
                'message': 'Quận/huyện không tồn tại'
            }, status=status.HTTP_404_NOT_FOUND)
class AddressListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Lấy danh sách địa chỉ của người dùng đã đăng nhập"""
        addresses = Address.objects.filter(user=request.user).order_by('-is_default', '-created_at')
        serializer = AddressSerializer(addresses, many=True)

        return Response({
            'status': 'success',
            'message': 'Danh sách địa chỉ được lấy thành công',
            'data': {
                'addresses': serializer.data
            }
        })

    # core/views.py (tiếp tục)
    def post(self, request):
        """Tạo địa chỉ mới cho người dùng đã đăng nhập"""
        serializer = AddressSerializer(data=request.data)

        if serializer.is_valid():
            # Kiểm tra xem địa chỉ này có được đánh dấu là mặc định không
            is_default = serializer.validated_data.get('is_default', False)

            # Nếu địa chỉ này là mặc định, đặt tất cả các địa chỉ khác thành không mặc định
            if is_default:
                Address.objects.filter(user=request.user).update(is_default=False)
            # Nếu không có địa chỉ nào, đặt địa chỉ này làm mặc định
            elif not Address.objects.filter(user=request.user).exists():
                serializer.validated_data['is_default'] = True

            # Lưu địa chỉ mới
            address = serializer.save(user=request.user)

            return Response({
                'status': 'success',
                'message': 'Địa chỉ đã được tạo thành công',
                'data': AddressSerializer(address).data
            }, status=status.HTTP_201_CREATED)

        return Response({
            'status': 'error',
            'message': 'Không thể tạo địa chỉ',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


# core/views.py
class AddressDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, pk, user):
        """Kiểm tra và lấy địa chỉ dựa trên ID và người dùng"""
        try:
            return Address.objects.get(pk=pk, user=user)
        except Address.DoesNotExist:
            return None

    def get(self, request, pk):
        """Lấy chi tiết một địa chỉ"""
        address = self.get_object(pk, request.user)

        if not address:
            return Response({
                'status': 'error',
                'message': 'Địa chỉ không tồn tại hoặc không thuộc về bạn'
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = AddressSerializer(address)
        return Response({
            'status': 'success',
            'message': 'Lấy thông tin địa chỉ thành công',
            'data': serializer.data
        })

    # core/views.py (tiếp tục AddressDetailView)
    def put(self, request, pk):
        """Cập nhật thông tin địa chỉ"""
        address = self.get_object(pk, request.user)

        if not address:
            return Response({
                'status': 'error',
                'message': 'Địa chỉ không tồn tại hoặc không thuộc về bạn'
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = AddressSerializer(address, data=request.data)

        if serializer.is_valid():
            # Kiểm tra xem địa chỉ này có được đánh dấu là mặc định không
            is_default = serializer.validated_data.get('is_default', False)

            # Nếu địa chỉ này là mặc định, đặt tất cả các địa chỉ khác thành không mặc định
            if is_default and not address.is_default:
                Address.objects.filter(user=request.user).exclude(pk=pk).update(is_default=False)

            # Lưu địa chỉ đã cập nhật
            updated_address = serializer.save()

            return Response({
                'status': 'success',
                'message': 'Địa chỉ đã được cập nhật thành công',
                'data': AddressSerializer(updated_address).data
            })

        return Response({
            'status': 'error',
            'message': 'Không thể cập nhật địa chỉ',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    # core/views.py (tiếp tục AddressDetailView)
    def delete(self, request, pk):
        """Xóa địa chỉ"""
        address = self.get_object(pk, request.user)

        if not address:
            return Response({
                'status': 'error',
                'message': 'Địa chỉ không tồn tại hoặc không thuộc về bạn'
            }, status=status.HTTP_404_NOT_FOUND)

        # Kiểm tra đây có phải là địa chỉ mặc định không
        is_default = address.is_default

        # Xóa địa chỉ
        address.delete()

        # Nếu đây là địa chỉ mặc định và còn các địa chỉ khác, đặt địa chỉ đầu tiên làm mặc định
        if is_default:
            addresses = Address.objects.filter(user=request.user).order_by('created_at')
            if addresses.exists():
                first_address = addresses.first()
                first_address.is_default = True
                first_address.save()

        return Response({
            'status': 'success',
            'message': 'Địa chỉ đã được xóa thành công'
        })


# core/views.py
class SetDefaultAddressView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        """Đặt một địa chỉ làm mặc định"""
        try:
            address = Address.objects.get(pk=pk, user=request.user)
        except Address.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'Địa chỉ không tồn tại hoặc không thuộc về bạn'
            }, status=status.HTTP_404_NOT_FOUND)

        # Đặt tất cả các địa chỉ thành không mặc định
        Address.objects.filter(user=request.user).update(is_default=False)

        # Đặt địa chỉ này làm mặc định
        address.is_default = True
        address.save()

        return Response({
            'status': 'success',
            'message': 'Địa chỉ đã được đặt làm mặc định',
            'data': {
                'id': address.id,
                'is_default': True
            }
        })
# Public APIs - No authentication required
class UserRegistrationView(APIView):
    permission_classes = [permissions.AllowAny]  # Public API
    
    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            
            # Generate OTP and send email using OTPManager
            otp_code = OTPManager.generate_otp(user.email)
            send_otp_email(user, otp_code)
            
            return APIResponse.success(
                data={"email": user.email, "role": user.role},
                message="Đăng ký thành công. Vui lòng kiểm tra email để lấy mã xác minh.",
                status_code=status.HTTP_201_CREATED
            )
        return APIResponse.error(
            message="Registration failed",
            errors=serializer.errors,
            status_code=status.HTTP_400_BAD_REQUEST
        )

class OTPVerificationView(APIView):
    permission_classes = [permissions.AllowAny]  # Public API
    
    def post(self, request):
        serializer = OTPVerificationSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            otp_code = serializer.validated_data['otp_code']
            
            # Validate OTP using OTPManager
            if OTPManager.validate_otp(email, otp_code):
                user = User.objects.get(email=email)
                
                # Activate user account
                user.status = 'active'
                user.save()
                
                return APIResponse.success(
                    data={"status": user.status},
                    message="Xác minh tài khoản thành công. Bây giờ bạn có thể đăng nhập.",
                    status_code=status.HTTP_200_OK
                )
            
            return APIResponse.error(
                message="Mã OTP không hợp lệ hoặc đã hết hạn.",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        return APIResponse.error(
            message="Xác minh không thành công.",
            errors=serializer.errors,
            status_code=status.HTTP_400_BAD_REQUEST
        )

class ResendOTPView(APIView):
    permission_classes = [permissions.AllowAny]  # Public API
    
    def post(self, request):
        email = request.data.get('email')
        if not email:
            return APIResponse.error(
                errors={"email": "Trường này là bắt buộc."},
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return APIResponse.error(
                errors={"email": "Người dùng có email này không tồn tại."},
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        if user.status == 'active':
            return APIResponse.error(
                message="Người dùng đã được xác minh.",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        # Generate a new OTP and send email
        otp_code = OTPManager.generate_otp(user.email)
        send_otp_email(user, otp_code)
        
        return APIResponse.success(
            data={"email": user.email},
            message="Mã xác minh đã được gửi tới email của bạn.",
            status_code=status.HTTP_200_OK
        )

class LoginView(APIView):
    permission_classes = [permissions.AllowAny]  # Public API
    
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            
            # Generate tokens
            refresh = RefreshToken.for_user(user)
            
            # Add custom claims to the token
            refresh['user_id'] = str(user.id)
            refresh['role'] = user.role
            
            return APIResponse.success(
                data={
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                    "user": {
                        "id": user.id,
                        "email": user.email,
                        "full_name": user.full_name,
                        "role": user.role
                    }
                },
                message="Đăng nhập thành công",
                status_code=status.HTTP_200_OK
            )
        
        return APIResponse.error(
            message="Đăng nhập không thành công.",
            errors=serializer.errors,
            status_code=status.HTTP_400_BAD_REQUEST
        )

# Protected API example - Requires authentication (Bearer token)
class UserProfileView(APIView):
    # No need to specify permission_classes here since IsAuthenticated is the default
    def get(self, request):
        user = request.user
        return APIResponse.success(
            data={
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "phone": user.phone,
                "role": user.role,
                "status": user.status
            },
            message="Hồ sơ đã được lấy lại thành công",
            status_code=status.HTTP_200_OK
        )


class UserProfileUpdateView(APIView):
    """View for updating user profile information"""
    permission_classes = [permissions.IsAuthenticated]

    def put(self, request):
        serializer = UserUpdateSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return APIResponse.success(
                data=serializer.data,
                message="Profile updated successfully.",
                status_code=status.HTTP_200_OK
            )
        return APIResponse.error(
            message="Profile update failed.",
            errors=serializer.errors,
            status_code=status.HTTP_400_BAD_REQUEST
        )


class ChangePasswordView(APIView):
    """View for changing user password"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user

            # Check if current password is correct
            if not user.check_password(serializer.validated_data['current_password']):
                return APIResponse.error(
                    message="Password change failed.",
                    errors={"current_password": "Current password is incorrect."},
                    status_code=status.HTTP_400_BAD_REQUEST
                )

            # Set new password
            user.set_password(serializer.validated_data['new_password'])
            user.save()

            return APIResponse.success(
                message="Password changed successfully. Please login again with your new password.",
                status_code=status.HTTP_200_OK
            )

        return APIResponse.error(
            message="Password change failed.",
            errors=serializer.errors,
            status_code=status.HTTP_400_BAD_REQUEST
        )


class DeleteAccountView(APIView):
    """View for deleting user account"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = DeleteAccountSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user

            # Verify password before deleting account
            if not user.check_password(serializer.validated_data['password']):
                return APIResponse.error(
                    message="Account deletion failed.",
                    errors={"password": "Password is incorrect."},
                    status_code=status.HTTP_400_BAD_REQUEST
                )

            # Proceed with account deletion
            user_email = user.email
            user.delete()

            return APIResponse.success(
                data={"email": user_email},
                message="Your account has been permanently deleted.",
                status_code=status.HTTP_200_OK
            )

        return APIResponse.error(
            message="Account deletion failed.",
            errors=serializer.errors,
            status_code=status.HTTP_400_BAD_REQUEST
        )


class ForgotPasswordRequestView(APIView):
    """View for initiating password reset process"""
    permission_classes = [permissions.AllowAny]  # Public API

    def post(self, request):
        serializer = ForgotPasswordRequestSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']

            try:
                user = User.objects.get(email=email)

                # Generate OTP for password reset
                otp_code = OTPManager.generate_otp(email)

                # Send password reset email
                send_password_reset_email(user, otp_code)

                return APIResponse.success(
                    data={"email": email},
                    message="Password reset instructions have been sent to your email.",
                    status_code=status.HTTP_200_OK
                )
            except User.DoesNotExist:
                # For security reasons, we still return a success response
                # even if the email doesn't exist in our database
                return APIResponse.success(
                    message="If your email exists in our system, password reset instructions have been sent.",
                    status_code=status.HTTP_200_OK
                )

        return APIResponse.error(
            message="Failed to process password reset request.",
            errors=serializer.errors,
            status_code=status.HTTP_400_BAD_REQUEST
        )


class ResetPasswordView(APIView):
    """View for resetting password using OTP"""
    permission_classes = [permissions.AllowAny]  # Public API

    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            otp_code = serializer.validated_data['otp_code']
            new_password = serializer.validated_data['new_password']

            # Validate OTP using OTPManager
            if OTPManager.validate_otp(email, otp_code):
                user = User.objects.get(email=email)

                # Set new password
                user.set_password(new_password)
                user.save()

                # Delete the OTP after successful password reset
                try:
                    otp = OTP.objects.get(user=user, code=otp_code)
                    otp.delete()
                except OTP.DoesNotExist:
                    pass

                return APIResponse.success(
                    message="Your password has been reset successfully. You can now log in with your new password.",
                    status_code=status.HTTP_200_OK
                )

            return APIResponse.error(
                message="Invalid or expired OTP code.",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        return APIResponse.error(
            message="Password reset failed.",
            errors=serializer.errors,
            status_code=status.HTTP_400_BAD_REQUEST
        )


class IsAdminUser(permissions.BasePermission):
    """
    Custom permission to only allow admin users to access the view.
    """

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'admin'


class AdminUserListCreateView(APIView):
    """View for admin to list all users or create a new user"""
    permission_classes = [IsAdminUser]

    def get(self, request):
        """Get list of all users with filtering options"""
        users = User.objects.all().order_by('-created_at')

        # Filtering options
        status = request.query_params.get('status')
        role = request.query_params.get('role')
        search = request.query_params.get('search')

        if status:
            users = users.filter(status=status)

        if role:
            users = users.filter(role=role)

        if search:
            users = users.filter(
                models.Q(email__icontains=search) |
                models.Q(full_name__icontains=search) |
                models.Q(phone__icontains=search)
            )

        # Pagination
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 10))

        paginator = Paginator(users, page_size)
        try:
            users_page = paginator.page(page)
        except (PageNotAnInteger, EmptyPage):
            users_page = paginator.page(1)

        serializer = AdminUserListSerializer(users_page, many=True)

        return Response({
            'status': 'success',
            'message': 'Danh sách người dùng được lấy thành công',
            'data': {
                'users': serializer.data,
                'pagination': {
                    'total': paginator.count,
                    'pages': paginator.num_pages,
                    'current_page': page,
                    'page_size': page_size
                }
            }
        })

    def post(self, request):
        """Create a new user by admin"""
        serializer = AdminUserCreateSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()

            return Response({
                'status': 'success',
                'message': 'Tạo người dùng thành công',
                'data': AdminUserDetailSerializer(user).data
            }, status=status.HTTP_201_CREATED)

        return Response({
            'status': 'error',
            'message': 'Không thể tạo người dùng',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class AdminUserDetailView(APIView):
    """View for admin to retrieve, update or delete a user"""
    permission_classes = [IsAdminUser]

    def get_object(self, pk):
        try:
            return User.objects.get(pk=pk)
        except User.DoesNotExist:
            raise Http404

    def get(self, request, user_id):
        """Get details of a specific user"""
        user = self.get_object(user_id)
        serializer = AdminUserDetailSerializer(user)

        return Response({
            'status': 'success',
            'message': 'Thông tin người dùng được lấy thành công',
            'data': serializer.data
        })

    def put(self, request, user_id):
        """Update a user's information"""
        user = self.get_object(user_id)
        serializer = AdminUserUpdateSerializer(user, data=request.data, partial=True)

        if serializer.is_valid():
            updated_user = serializer.save()

            return Response({
                'status': 'success',
                'message': 'Cập nhật thông tin người dùng thành công',
                'data': AdminUserDetailSerializer(updated_user).data
            })

        return Response({
            'status': 'error',
            'message': 'Không thể cập nhật thông tin người dùng',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, user_id):
        """Delete a user"""
        user = self.get_object(user_id)

        # Check if admin is trying to delete themself
        if user.id == request.user.id:
            return Response({
                'status': 'error',
                'message': 'Bạn không thể xóa tài khoản của chính mình'
            }, status=status.HTTP_400_BAD_REQUEST)

        user.delete()

        return Response({
            'status': 'success',
            'message': 'Xóa người dùng thành công'
        }, status=status.HTTP_200_OK)


class AdminResetUserPasswordView(APIView):
    """View for admin to reset a user's password"""
    permission_classes = [IsAdminUser]

    def post(self, request, user_id):
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'Người dùng không tồn tại'
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = AdminResetUserPasswordSerializer(data=request.data)
        if serializer.is_valid():
            # Set new password
            user.set_password(serializer.validated_data['new_password'])
            user.save()

            return Response({
                'status': 'success',
                'message': 'Đặt lại mật khẩu thành công'
            })

        return Response({
            'status': 'error',
            'message': 'Không thể đặt lại mật khẩu',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class AdminUserStatusBulkUpdateView(APIView):
    """View for admin to update multiple users' status at once"""
    permission_classes = [IsAdminUser]

    def post(self, request):
        user_ids = request.data.get('user_ids', [])
        new_status = request.data.get('status')

        if not user_ids or not new_status:
            return Response({
                'status': 'error',
                'message': 'Thiếu thông tin bắt buộc',
                'errors': {
                    'user_ids': 'Danh sách ID người dùng là bắt buộc',
                    'status': 'Trạng thái mới là bắt buộc'
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        if new_status not in [s[0] for s in User.STATUS_CHOICES]:
            return Response({
                'status': 'error',
                'message': 'Trạng thái không hợp lệ',
                'errors': {
                    'status': f"Trạng thái phải là một trong {[s[0] for s in User.STATUS_CHOICES]}"
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        # Update users
        updated_count = User.objects.filter(id__in=user_ids).update(status=new_status)

        return Response({
            'status': 'success',
            'message': f'Đã cập nhật trạng thái của {updated_count} người dùng thành {new_status}',
            'data': {
                'updated_count': updated_count
            }
        })


class AdminUserStatisticsView(APIView):
    """View for admin to get user statistics"""
    permission_classes = [IsAdminUser]

    def get(self, request):
        # Total users count
        total_users = User.objects.count()

        # Users by role
        users_by_role = {
            'customer': User.objects.filter(role='customer').count(),
            'shop_owner': User.objects.filter(role='shop_owner').count(),
            'admin': User.objects.filter(role='admin').count()
        }

        # Users by status
        users_by_status = {
            'active': User.objects.filter(status='active').count(),
            'inactive': User.objects.filter(status='inactive').count(),
            'banned': User.objects.filter(status='banned').count()
        }

        # New users in the last 7 days
        seven_days_ago = timezone.now() - timezone.timedelta(days=7)
        new_users_last_7_days = User.objects.filter(created_at__gte=seven_days_ago).count()

        # New users in the last 30 days
        thirty_days_ago = timezone.now() - timezone.timedelta(days=30)
        new_users_last_30_days = User.objects.filter(created_at__gte=thirty_days_ago).count()

        return Response({
            'status': 'success',
            'message': 'Thống kê người dùng được lấy thành công',
            'data': {
                'total_users': total_users,
                'users_by_role': users_by_role,
                'users_by_status': users_by_status,
                'new_users_last_7_days': new_users_last_7_days,
                'new_users_last_30_days': new_users_last_30_days
            }
        })


class AdminBulkDeleteUsersView(APIView):
    """View for admin to delete multiple users at once"""
    permission_classes = [IsAdminUser]

    def post(self, request):
        user_ids = request.data.get('user_ids', [])

        if not user_ids:
            return Response({
                'status': 'error',
                'message': 'Thiếu thông tin bắt buộc',
                'errors': {
                    'user_ids': 'Danh sách ID người dùng là bắt buộc'
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        # Prevent admin from deleting their own account
        if request.user.id in user_ids:
            return Response({
                'status': 'error',
                'message': 'Bạn không thể xóa tài khoản của chính mình',
                'errors': {
                    'user_ids': 'Danh sách chứa ID của tài khoản hiện tại'
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        # Check if any of the users to delete are admins
        admin_users = User.objects.filter(id__in=user_ids, role='admin').count()
        if admin_users > 0:
            # Option 1: Prevent deleting admin accounts
            return Response({
                'status': 'error',
                'message': 'Không thể xóa tài khoản admin',
                'errors': {
                    'user_ids': 'Danh sách chứa ID của tài khoản admin'
                }
            }, status=status.HTTP_400_BAD_REQUEST)

            # Option 2: Allow deleting admin accounts but warn about it
            # return Response({
            #     'status': 'warning',
            #     'message': f'Cảnh báo: Bạn đang xóa {admin_users} tài khoản admin. Việc này có thể gây ra vấn đề bảo mật.',
            #     'data': {
            #         'admin_count': admin_users
            #     }
            # }, status=status.HTTP_200_OK)

        # Get emails of users to be deleted (for logging or reporting)
        emails_to_delete = list(User.objects.filter(id__in=user_ids).values_list('email', flat=True))

        # Delete users
        deleted_count, _ = User.objects.filter(id__in=user_ids).delete()

        return Response({
            'status': 'success',
            'message': f'Đã xóa {deleted_count} tài khoản người dùng thành công',
            'data': {
                'deleted_count': deleted_count,
                'deleted_emails': emails_to_delete
            }
        }, status=status.HTTP_200_OK)