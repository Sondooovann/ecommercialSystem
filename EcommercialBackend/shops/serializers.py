from django.contrib.auth import get_user_model
from rest_framework import serializers
# Import your existing serializers
from .models import Shop, ShopSetting, ShopFollower, SizeChart

User = get_user_model()

# shops/serializers.py
class ShopAnalyticsSerializer(serializers.Serializer):
    overview = serializers.DictField()
    salesData = serializers.ListField()
    productPerformance = serializers.ListField()
    customerSegments = serializers.ListField()
    orderStatus = serializers.ListField()

class UserAccountSerializer(serializers.ModelSerializer):
    """Serializer to return basic user account information"""
    class Meta:
        model = User
        fields = ['id', 'email', 'full_name', 'avatar', 'phone', 'role', 'status', 'created_at']
        read_only_fields = fields  # Make all fields read-only

class ShopCreateSerializer(serializers.ModelSerializer):
    shipping_policy = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    return_policy = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    bank_account_info = serializers.CharField(required=False, allow_null=True, allow_blank=True)

    class Meta:
        model = Shop
        fields = ['name', 'description', 'logo', 'banner', 'shipping_policy', 'return_policy', 'bank_account_info']

    def create(self, validated_data):
        # Extract ShopSetting fields
        shipping_policy = validated_data.pop('shipping_policy', None)
        return_policy = validated_data.pop('return_policy', None)
        bank_account_info = validated_data.pop('bank_account_info', None)

        # Get the user from the context
        user = self.context['request'].user

        # Create the shop with the owner set to the current user
        shop = Shop.objects.create(owner=user, **validated_data)

        # Create shop settings
        ShopSetting.objects.create(
            shop=shop,
            shipping_policy=shipping_policy,
            return_policy=return_policy,
            bank_account_info=bank_account_info
        )

        return shop

# Add these serializers to your existing file

class ShopSettingSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShopSetting
        fields = ['shipping_policy', 'return_policy', 'bank_account_info']


class ShopDetailSerializer(serializers.ModelSerializer):
    owner = serializers.SerializerMethodField()
    settings = ShopSettingSerializer(source='shopsetting', read_only=True)
    follower_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Shop
        fields = ['id', 'name', 'description', 'logo', 'banner', 'status', 
                  'rating', 'owner', 'created_at', 'updated_at', 'settings',
                  'follower_count']
    
    def get_owner(self, obj):
        return {
            'id': obj.owner.id,
            'username': obj.owner.full_name,
            'email': obj.owner.email
        }
    
    def get_follower_count(self, obj):
        return obj.followers.count()


class ShopListSerializer(serializers.ModelSerializer):
    owner_name = serializers.CharField(source='owner.username', read_only=True)
    
    class Meta:
        model = Shop
        fields = ['id', 'name', 'logo', 'banner', 'status', 'rating', 'owner_name', 'created_at']


class ShopFollowerSerializer(serializers.ModelSerializer):
    """Serializer for shop followers with detailed user information"""
    user = UserAccountSerializer(read_only=True)
    
    class Meta:
        model = ShopFollower
        fields = ['id', 'user', 'shop', 'created_at']
        read_only_fields = fields


class ShopSettingUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShopSetting
        fields = ['shipping_policy', 'return_policy', 'bank_account_info']

class ShopUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shop
        fields = ['name', 'description', 'status']

class SizeChartSerializer(serializers.ModelSerializer):
    class Meta:
        model = SizeChart
        fields = ['id', 'shop', 'name', 'chart_data', 'created_at', 'updated_at']
        read_only_fields = ['shop']

class ShopFollowCheckSerializer(serializers.Serializer):
    """Serializer to check if a user is following a shop"""
    shop_id = serializers.IntegerField(required=True)
    is_following = serializers.SerializerMethodField()

    def get_is_following(self, obj):
        user = self.context.get('request').user
        shop_id = obj.get('shop_id')

        # Handle anonymous users
        if not user.is_authenticated:
            return False

        try:
            return ShopFollower.objects.filter(user=user, shop_id=shop_id).exists()
        except Exception:
            return False


class AdminShopListSerializer(serializers.ModelSerializer):
    """Serializer for admin to list shops with additional information"""
    owner_details = serializers.SerializerMethodField()
    product_count = serializers.SerializerMethodField()
    follower_count = serializers.SerializerMethodField()

    class Meta:
        model = Shop
        fields = ['id', 'name', 'logo', 'status', 'rating', 'owner_details',
                  'product_count', 'follower_count', 'created_at', 'updated_at']

    def get_owner_details(self, obj):
        return {
            'id': obj.owner.id,
            'email': obj.owner.email,
            'full_name': obj.owner.full_name,
            'status': obj.owner.status
        }

    def get_product_count(self, obj):
        return obj.products.count()

    def get_follower_count(self, obj):
        return obj.followers.count()


class AdminShopDetailSerializer(serializers.ModelSerializer):
    """Serializer for admin to view complete shop details"""
    owner = UserAccountSerializer(read_only=True)
    settings = ShopSettingSerializer(source='shopsetting', read_only=True)
    product_count = serializers.SerializerMethodField()
    follower_count = serializers.SerializerMethodField()

    class Meta:
        model = Shop
        fields = ['id', 'name', 'description', 'logo', 'banner', 'status',
                  'rating', 'owner', 'created_at', 'updated_at', 'settings',
                  'product_count', 'follower_count']

    def get_product_count(self, obj):
        return obj.products.count()

    def get_follower_count(self, obj):
        return obj.followers.count()


class AdminShopUpdateSerializer(serializers.ModelSerializer):
    """Serializer for admin to update shop details"""

    class Meta:
        model = Shop
        fields = ['name', 'description', 'status']


class AdminShopSettingsUpdateSerializer(serializers.ModelSerializer):
    """Serializer for admin to update shop settings"""

    class Meta:
        model = ShopSetting
        fields = ['shipping_policy', 'return_policy', 'bank_account_info']