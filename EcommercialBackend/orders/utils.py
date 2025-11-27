from products.models import ProductVariant
from products.models import Product, ProductVariant
from django.db.models import Sum

def decrease_product_stock(product, quantity):
    """
    Giảm số lượng tồn kho của sản phẩm và cập nhật trạng thái nếu cần
    """
    product.stock -= quantity
    
    # Cập nhật trạng thái sản phẩm nếu hết hàng
    if product.stock <= 0:
        product.status = 'out_of_stock'
        product.save(update_fields=['stock', 'status'])
    else:
        product.save(update_fields=['stock'])

def increase_product_stock(product, quantity):
    """
    Tăng số lượng tồn kho của sản phẩm và cập nhật trạng thái nếu cần
    """
    product.stock += quantity
    
    # Cập nhật trạng thái sản phẩm nếu từ out_of_stock sang có hàng
    if product.status == 'out_of_stock' and product.stock > 0:
        product.status = 'active'
        product.save(update_fields=['stock', 'status'])
    else:
        product.save(update_fields=['stock'])

def check_variant_availability(variant, quantity_needed):
    """
    Kiểm tra xem variant có đủ số lượng tồn kho không
    Trả về (bool, str): (đủ hàng hay không, thông báo lỗi nếu không đủ)
    """
    if variant.stock < quantity_needed:
        product_name = variant.product.name
        return False, f"Sản phẩm '{product_name}' không đủ tồn kho. Hiện tại chỉ còn {variant.stock} sản phẩm."
    return True, ""

def update_product_status_based_on_variants(product):
    """
    Cập nhật trạng thái sản phẩm dựa trên tồn kho của tất cả variant
    """
    # Tính tổng tồn kho của tất cả variant
    total_variant_stock = product.variants.aggregate(Sum('stock'))['stock__sum'] or 0
    
    # Cập nhật trạng thái sản phẩm nếu cần
    if total_variant_stock == 0 and product.status != 'out_of_stock':
        product.status = 'out_of_stock'
        product.save(update_fields=['status'])
    elif total_variant_stock > 0 and product.status == 'out_of_stock':
        product.status = 'active'
        product.save(update_fields=['status'])
def decrease_variant_stock(variant, quantity):
    """Decrease stock for a product variant"""
    variant.stock -= quantity
    variant.save()

    # Update product stock status if needed
    product = variant.product
    all_variants = product.variants.all()
    total_stock = sum(v.stock for v in all_variants)

    if total_stock == 0 and product.status != 'out_of_stock':
        product.status = 'out_of_stock'
        product.save()

def increase_variant_stock(variant, quantity):
    """Increase stock for a product variant"""
    variant.stock += quantity
    variant.save()

    # Update product stock status if needed
    product = variant.product
    if product.status == 'out_of_stock' and variant.stock > 0:
        product.status = 'active'
        product.save()