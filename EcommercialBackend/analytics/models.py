from django.db import models
from shops.models import Shop
from products.models import Product


class ShopAnalytic(models.Model):
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name='analytics')
    date = models.DateField()
    views = models.IntegerField(default=0)
    orders = models.IntegerField(default=0)
    revenue = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'shop_analytics'
        unique_together = ('shop', 'date')

    def __str__(self):
        return f"Analytics for {self.shop.name} on {self.date}"


class ProductAnalytic(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='analytics')
    date = models.DateField()
    views = models.IntegerField(default=0)
    add_to_carts = models.IntegerField(default=0)
    orders = models.IntegerField(default=0)
    revenue = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'product_analytics'
        unique_together = ('product', 'date')

    def __str__(self):
        return f"Analytics for {self.product.name} on {self.date}"