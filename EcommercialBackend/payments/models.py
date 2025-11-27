from django.db import models
from orders.models import Order


class Payment(models.Model):
    PROVIDER_CHOICES = (
        ('banking', 'Banking'),
        ('momo', 'MoMo'),
        ('zalopay', 'ZaloPay'),
        ('paypal', 'PayPal'),
        ('stripe', 'Stripe'),
    )

    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    )

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    provider = models.CharField(max_length=20, choices=PROVIDER_CHOICES)
    transaction_id = models.CharField(max_length=255, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_data = models.TextField(blank=True, null=True)  # JSON data
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'payments'

    def __str__(self):
        return f"Payment for Order #{self.order.id} - {self.amount}"