from django.db import models
from core.models import User


class Shop(models.Model):
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('banned', 'Banned'),
    )

    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='shops')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    logo = models.CharField(max_length=255, blank=True, null=True)
    banner = models.CharField(max_length=255, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    rating = models.DecimalField(max_digits=2, decimal_places=1, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'shops'

    def __str__(self):
        return self.name


class ShopFollower(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='followed_shops')
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name='followers')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'shop_followers'
        unique_together = ('user', 'shop')

    def __str__(self):
        return f"{self.user.email} follows {self.shop.name}"


class ShopSetting(models.Model):
    shop = models.OneToOneField(Shop, on_delete=models.CASCADE, related_name='settings')
    shipping_policy = models.TextField(blank=True, null=True)
    return_policy = models.TextField(blank=True, null=True)
    bank_account_info = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'shop_settings'

    def __str__(self):
        return f"Settings for {self.shop.name}"


class SizeChart(models.Model):
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name='size_charts')
    name = models.CharField(max_length=100)
    category = models.ForeignKey('products.Category', on_delete=models.SET_NULL, null=True, related_name='size_charts')
    chart_data = models.TextField()  # JSON data
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'size_charts'

    def __str__(self):
        return f"{self.name} - {self.shop.name}"