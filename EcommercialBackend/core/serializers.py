from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import OTP
from core.models import Address
from core.models import Province, District, Ward

User = get_user_model()


# core/serializers.py
class ProvinceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Province
        fields = ['id', 'name', 'code']


class DistrictSerializer(serializers.ModelSerializer):
    province_name = serializers.CharField(source='province.name', read_only=True)

    class Meta:
        model = District
        fields = ['id', 'name', 'code', 'province_id', 'province_name']


class WardSerializer(serializers.ModelSerializer):
    district_name = serializers.CharField(source='district.name', read_only=True)

    class Meta:
        model = Ward
        fields = ['id', 'name', 'code', 'district_id', 'district_name']


class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = ['id', 'recipient_name', 'phone', 'province', 'district',
                  'ward', 'street_address', 'is_default', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    confirm_password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})

    class Meta:
        model = User
        fields = ['email', 'full_name', 'phone', 'password', 'confirm_password', 'role']

    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError({"confirm_password": "Mật khẩu không khớp."})

        valid_role = ['customer', 'shop_owner']
        if data['role'].lower() == 'admin':
            raise serializers.ValidationError({"role": "Không được phép giữ vai trò quản trị viên."})
        elif data['role'].lower() not in valid_role:
            raise serializers.ValidationError({"role": "Vai trò không hợp lệ."})

        return data

    def create(self, validated_data):
        validated_data.pop('confirm_password')
        user = User.objects.create_user(
            email=validated_data['email'],
            full_name=validated_data['full_name'],
            phone=validated_data.get('phone'),
            status='inactive',
            password=validated_data['password'],
            role=validated_data['role'].lower(),
        )
        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, style={'input_type': 'password'})

    def validate(self, data):
        email = data.get('email')
        password = data.get('password')

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError({"non_field_errors": "Thông tin đăng nhập không hợp lệ."})

        # Check if user is activated
        if user.status != 'active':
            raise serializers.ValidationError(
                {"non_field_errors": "Tài khoản chưa được kích hoạt. Vui lòng xác minh email của bạn.",
                 "code": "1001"})

        # Verify password
        if not user.check_password(password):
            raise serializers.ValidationError({"non_field_errors": "Thông tin đăng nhập không hợp lệ."})

        data['user'] = user
        return data


class OTPVerificationSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp_code = serializers.CharField(max_length=6)

    def validate(self, data):
        try:
            user = User.objects.get(email=data['email'])
        except User.DoesNotExist:
            raise serializers.ValidationError({"email": "Người dùng có email này không tồn tại."})

        try:
            otp = OTP.objects.get(user=user, code=data['otp_code'])
        except OTP.DoesNotExist:
            raise serializers.ValidationError({"otp_code": "Mã OTP không hợp lệ."})

        if not otp.is_valid():
            otp.delete()
            raise serializers.ValidationError({"otp_code": "Mã OTP đã hết hạn. Vui lòng yêu cầu mã mới."})

        return data


class UserUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating user information"""

    class Meta:
        model = User
        fields = ['full_name', 'phone']

    def validate_phone(self, value):
        if value and not value.isdigit():
            raise serializers.ValidationError("Số điện thoại chỉ được chứa chữ số.")
        return value


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for password change"""
    current_password = serializers.CharField(required=True, style={'input_type': 'password'})
    new_password = serializers.CharField(required=True, style={'input_type': 'password'})
    confirm_password = serializers.CharField(required=True, style={'input_type': 'password'})

    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError({"confirm_password": "Mật khẩu mới không khớp."})
        return data


class DeleteAccountSerializer(serializers.Serializer):
    """Serializer for account deletion"""
    password = serializers.CharField(required=True, style={'input_type': 'password'})


class ForgotPasswordRequestSerializer(serializers.Serializer):
    """Serializer for initiating a password reset"""
    email = serializers.EmailField(required=True)

    def validate_email(self, value):
        try:
            User.objects.get(email=value)
        except User.DoesNotExist:
            # For security reasons, we don't want to reveal whether the email exists
            # But we'll still validate it on the backend
            pass
        return value


class ResetPasswordSerializer(serializers.Serializer):
    """Serializer for resetting password using OTP"""
    email = serializers.EmailField(required=True)
    otp_code = serializers.CharField(required=True, max_length=6)
    new_password = serializers.CharField(required=True, style={'input_type': 'password'})
    confirm_password = serializers.CharField(required=True, style={'input_type': 'password'})

    def validate(self, data):
        # Validate that the passwords match
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError({"confirm_password": "Mật khẩu không khớp."})

        # Validate user exists
        try:
            user = User.objects.get(email=data['email'])
        except User.DoesNotExist:
            raise serializers.ValidationError({"email": "Người dùng có email này không tồn tại."})

        # Validate OTP
        try:
            otp = OTP.objects.get(user=user, code=data['otp_code'])
        except OTP.DoesNotExist:
            raise serializers.ValidationError({"otp_code": "Mã OTP không hợp lệ."})

        if not otp.is_valid():
            otp.delete()
            raise serializers.ValidationError({"otp_code": "Mã OTP đã hết hạn. Vui lòng yêu cầu mã mới."})

        return data

class CustomerInfoSerializer(serializers.ModelSerializer):
    """Serializer để hiển thị thông tin khách hàng trong đơn hàng"""
    class Meta:
        model = User
        fields = ['id', 'full_name', 'email', 'phone', 'avatar']
        read_only_fields = fields

class AdminUserListSerializer(serializers.ModelSerializer):
    """Serializer for admin to list all users"""
    class Meta:
        model = User
        fields = ['id', 'email', 'full_name', 'phone', 'role', 'status', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class AdminUserDetailSerializer(serializers.ModelSerializer):
    """Serializer for admin to view and update user details"""
    addresses = AddressSerializer(many=True, read_only=True)

    class Meta:
        model = User
        fields = ['id', 'email', 'full_name', 'phone', 'avatar', 'role', 'status',
                  'is_staff', 'is_superuser', 'created_at', 'updated_at', 'addresses']
        read_only_fields = ['id', 'created_at', 'updated_at']


class AdminUserCreateSerializer(serializers.ModelSerializer):
    """Serializer for admin to create new users"""
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    confirm_password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})

    class Meta:
        model = User
        fields = ['email', 'full_name', 'phone', 'role', 'status', 'password', 'confirm_password', 'is_staff']

    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError({"confirm_password": "Mật khẩu không khớp."})

        return data

    def create(self, validated_data):
        validated_data.pop('confirm_password')
        password = validated_data.pop('password')

        user = User.objects.create(**validated_data)
        user.set_password(password)
        user.save()

        return user


class AdminUserUpdateSerializer(serializers.ModelSerializer):
    """Serializer for admin to update user details"""
    class Meta:
        model = User
        fields = ['full_name', 'phone', 'avatar', 'role', 'status', 'is_staff']


class AdminResetUserPasswordSerializer(serializers.Serializer):
    """Serializer for admin to reset a user's password"""
    new_password = serializers.CharField(required=True, style={'input_type': 'password'})
    confirm_password = serializers.CharField(required=True, style={'input_type': 'password'})

    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError({"confirm_password": "Mật khẩu không khớp."})
        return data