import { Component, OnInit, Output, EventEmitter, HostListener } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { CartService } from '../../../core/services/cart.service';
import { Cart, CartItem } from '../../../core/models/cart.model';
import { SafeHtmlPipe } from '../../pipes/pipe-html.pipe';
import { ICON_TRASH, ICON_CLOSE } from '../../../../assets/icons/icon';

@Component({
  selector: 'jhi-cart-modal',
  standalone: true,
  imports: [CommonModule, SafeHtmlPipe],
  templateUrl: './cart-modal.component.html',
  styleUrls: ['./cart-modal.component.scss']
})
export class CartModalComponent implements OnInit {
  @Output() close = new EventEmitter<void>();

  cart: Cart | null = null;
  loading = false;
  error = '';
  isVisible = false;

  protected readonly ICON_TRASH = ICON_TRASH;
  protected readonly ICON_CLOSE = ICON_CLOSE;

  constructor(
    private cartService: CartService,
    private router: Router
  ) {}

  ngOnInit(): void {
    this.loadCart();
    // Trigger animation
    setTimeout(() => {
      this.isVisible = true;
    }, 10);
  }

  @HostListener('document:keydown.escape', ['$event'])
  handleEscape(event: KeyboardEvent): void {
    this.closeModal();
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

  removeItem(itemId: number | undefined, event: Event): void {
    event.stopPropagation();
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

  viewAll(): void {
    this.closeModal();
    this.router.navigate(['/buyer/cart']);
  }

  closeModal(): void {
    this.isVisible = false;
    setTimeout(() => {
      this.close.emit();
    }, 300);
  }

  onBackdropClick(event: Event): void {
    if (event.target === event.currentTarget) {
      this.closeModal();
    }
  }

  formatPrice(price: string | number): string {
    const numPrice = typeof price === 'string' ? parseFloat(price) : price;
    return numPrice.toLocaleString('vi-VN') + '₫';
  }

  getTotalItemsText(): string {
    if (!this.cart) return '0 sản phẩm';
    const count = this.cart.total_items;
    return `${count} sản phẩm`;
  }

  getPlaceholderImage(): string {
   return "null";}

  onImageError(event: Event): void {
    const img = event.target as HTMLImageElement;
    img.src = this.getPlaceholderImage();
  }
}


