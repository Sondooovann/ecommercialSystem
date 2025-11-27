from django.db import models
from core.models import User
from products.models import Product
from orders.models import OrderItem



class Review(models.Model):
    STATUS_CHOICES = (
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    order_item = models.ForeignKey(OrderItem, on_delete=models.CASCADE, related_name='review')
    rating = models.IntegerField()
    comment = models.TextField(blank=True, null=True)
    images = models.TextField(blank=True, null=True)  # JSON array of image URLs
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='approved')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'reviews'
        unique_together = ('user', 'order_item')

    def __str__(self):
        return f"Review for {self.product.name} by {self.user.email}"

# reviews/models.py
from django.db import models
from core.models import User
from products.models import Product
from orders.models import OrderItem, Order

class ForbiddenWord(models.Model):
    word = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'forbidden_words'

    def __str__(self):
        return self.word

class OrderReview(models.Model):
    STATUS_CHOICES = (
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='order_reviews')
    rating = models.IntegerField()
    comment = models.TextField(blank=True, null=True)
    images = models.TextField(blank=True, null=True)  # JSON array of image URLs
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='approved')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'order_reviews'
        unique_together = ('user', 'order')  # Mỗi người dùng chỉ đánh giá một đơn hàng một lần

    def __str__(self):
        return f"Review for Order #{self.order.id} by {self.user.email}"

class ReviewLike(models.Model):
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='review_likes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'review_likes'
        unique_together = ('review', 'user')

    def __str__(self):
        return f"{self.user.email} likes {self.review.id}"