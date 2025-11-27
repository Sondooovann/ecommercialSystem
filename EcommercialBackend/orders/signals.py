from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db.models import F
from .models import OrderItem
from products.models import Product

@receiver(post_save, sender=OrderItem)
def update_product_sold_count(sender, instance, created, **kwargs):
    """
    Signal to update product sold count when order item status changes to 'delivered', 'received' or 'received_reviewed'
    """
    # List of statuses that indicate a completed sale
    completed_statuses = ['delivered', 'received', 'received_reviewed']
    
    # Check if status changed to a completed status
    if instance.status in completed_statuses:
        # Get the old instance from the database if it exists (to check status change)
        try:
            old_instance = OrderItem.objects.get(pk=instance.pk)
            old_status = old_instance.status
        except OrderItem.DoesNotExist:
            old_status = None
        
        # If this is a new completed status (not already counted)
        if old_status not in completed_statuses:
            # Update the product sold count
            Product.objects.filter(pk=instance.product.pk).update(
                sold_count=F('sold_count') + instance.quantity
            )
    
    # Handle cancellations or returns that need to reduce the sold count
    elif instance.status in ['cancelled', 'returned']:
        try:
            old_instance = OrderItem.objects.get(pk=instance.pk)
            old_status = old_instance.status
        except OrderItem.DoesNotExist:
            old_status = None
        
        # Only reduce count if it was previously in a completed state
        if old_status in completed_statuses:
            # Reduce the sold count
            Product.objects.filter(pk=instance.product.pk).update(
                sold_count=F('sold_count') - instance.quantity
            )