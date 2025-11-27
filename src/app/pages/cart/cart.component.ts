import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { CartService } from '../../core/services/cart.service';
import { Cart, CartItem } from '../../core/models/cart.model';
import { SafeHtmlPipe } from '../../shared/pipes/pipe-html.pipe';
import {ICON_BACK, ICON_MINUS, ICON_PLUS, ICON_TRASH} from '../../../assets/icons/icon';

@Component({
  selector: 'jhi-cart',
  standalone: true,
  imports: [CommonModule, SafeHtmlPipe],
  templateUrl: './cart.component.html',
  styleUrls: ['./cart.component.scss']
})
export class CartComponent implements OnInit {
  cart: Cart | null = null;
  loading = false;
  error = '';

  protected readonly ICON_TRASH = ICON_TRASH;
  protected readonly ICON_MINUS = ICON_MINUS;
  protected readonly ICON_PLUS = ICON_PLUS;
  protected readonly ICON_BACK = ICON_BACK;

  constructor(
    private cartService: CartService,
    private router: Router
  ) {}

  ngOnInit(): void {
    this.loadCart();
  }

  loadCart(): void {
    this.loading = true;
    this.error = '';
    this.cartService.getCart().subscribe({
      next: (response) => {
        if (response.success && response.data?.data) {
          this.cart = response.data.data;
        }
        this.loading = false;
      },
      error: (err) => {
        this.error = 'Không thể tải giỏ hàng. Vui lòng thử lại!';
        this.loading = false;
        console.error('Error loading cart:', err);
      }
    });
  }

  updateQuantity(item: CartItem, newQuantity: number): void {
    if (newQuantity < 1) return;

    if (item.id) {
      this.cartService.updateCartItem(item.id, newQuantity).subscribe({
        next: () => {
          this.loadCart();
        },
        error: (err) => {
          console.error('Error updating cart item:', err);
          this.error = 'Không thể cập nhật số lượng';
        }
      });
    }
  }

  removeItem(itemId: number | undefined): void {
    if (!itemId) return;

    if (confirm('Bạn có chắc muốn xóa sản phẩm này khỏi giỏ hàng?')) {
      this.cartService.removeFromCart(itemId).subscribe({
        next: () => {
          this.loadCart();
        },
        error: (err) => {
          console.error('Error removing cart item:', err);
          this.error = 'Không thể xóa sản phẩm';
        }
      });
    }
  }

  goBack(): void {
    this.router.navigate(['/']);
  }

  checkout(): void {
    if (this.cart && this.cart.total_items > 0) {
      this.router.navigate(['/buyer/checkout']);
    } else {
      alert('Giỏ hàng trống');
    }
  }

  formatPrice(price: string | number): string {
    const numPrice = typeof price === 'string' ? parseFloat(price) : price;
    return numPrice.toLocaleString('vi-VN') + '₫';
  }

  getGroupedByShop(): { shop_id: number; shop_name: string; items: CartItem[] }[] {
    if (!this.cart || !this.cart.items) return [];

    const grouped = new Map<number, { shop_id: number; shop_name: string; items: CartItem[] }>();

    this.cart.items.forEach(item => {
      const shopId = item.variant_details.shop_id;
      const shopName = item.variant_details.shop_name;

      if (!grouped.has(shopId)) {
        grouped.set(shopId, {
          shop_id: shopId,
          shop_name: shopName,
          items: []
        });
      }

      grouped.get(shopId)!.items.push(item);
    });

    return Array.from(grouped.values());
  }

  getPlaceholderImage(): string {
    // SVG placeholder image as data URL
    return 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCIgZmlsbD0iI2YwZjBmMCIvPjx0ZXh0IHg9IjUwJSIgeT0iNTAlIiBmb250LWZhbWlseT0iQXJpYWwiIGZvbnQtc2l6ZT0iMTQiIGZpbGw9IiM5OTkiIHRleHQtYW5jaG9yPSJtaWRkbGUiIGR5PSIuM2VtIj5ObyBJbWFnZTwvdGV4dD48L3N2Zz4=';
  }

  onImageError(event: Event): void {
    const img = event.target as HTMLImageElement;
    img.src = this.getPlaceholderImage();
  }
}


