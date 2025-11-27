import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, ActivatedRoute } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { CheckoutService } from '../../core/services/checkout.service';
import { CartService } from '../../core/services/cart.service';
import { Address } from '../../core/models/address.model';
import { Cart, CartItem } from '../../core/models/cart.model';
import { CreateOrderRequest } from '../../core/models/order.model';
import { SafeHtmlPipe } from '../../shared/pipes/pipe-html.pipe';
import { ICON_BACK, ICON_LOCATION_DOT } from '../../../assets/icons/icon';

interface GroupedCartItems {
  shop_id: number;
  shop_name: string;
  items: CartItem[];
  subtotal: number;
}

@Component({
  selector: 'jhi-checkout',
  standalone: true,
  imports: [CommonModule, FormsModule, SafeHtmlPipe],
  templateUrl: './checkout.component.html',
  styleUrls: ['./checkout.component.scss']
})
export class CheckoutComponent implements OnInit {
  addresses: Address[] = [];
  selectedAddress: Address | null = null;
  cart: Cart | null = null;
  selectedItems: CartItem[] = [];
  groupedItems: GroupedCartItems[] = [];

  paymentMethod: 'cod' | 'online' = 'cod';
  orderNotes = '';

  loading = false;
  loadingAddresses = false;
  error = '';

  // Shipping and totals
  shippingFee = 30000;
  totalProductAmount = 0;
  totalAmount = 0;

  protected readonly ICON_BACK = ICON_BACK;
  protected readonly ICON_LOCATION_DOT = ICON_LOCATION_DOT;

  constructor(
    private checkoutService: CheckoutService,
    private cartService: CartService,
    private router: Router,
    private route: ActivatedRoute
  ) {}

  ngOnInit(): void {
    this.loadData();
  }

  loadData(): void {
    this.loadAddresses();
    this.loadCart();
  }

  loadAddresses(): void {
    this.loadingAddresses = true;
    this.checkoutService.getAddresses().subscribe({
      next: (response) => {
        if (response.success && response.data?.data?.addresses) {
          this.addresses = response.data.data.addresses;
          // Tự động chọn địa chỉ mặc định
          this.selectedAddress = this.addresses.find(a => a.is_default) || this.addresses[0] || null;
        }
        this.loadingAddresses = false;
      },
      error: (err) => {
        console.error('Error loading addresses:', err);
        this.error = 'Không thể tải danh sách địa chỉ';
        this.loadingAddresses = false;
      }
    });
  }

  loadCart(): void {
    this.loading = true;
    this.cartService.getCart().subscribe({
      next: (response) => {
        if (response.success && response.data?.data) {
          this.cart = response.data.data;
          // Lấy tất cả items từ giỏ hàng để thanh toán
          this.selectedItems = this.cart.items || [];
          this.groupItemsByShop();
          this.calculateTotals();
        }
        this.loading = false;
      },
      error: (err) => {
        console.error('Error loading cart:', err);
        this.error = 'Không thể tải giỏ hàng';
        this.loading = false;
      }
    });
  }

  groupItemsByShop(): void {
    if (!this.selectedItems || this.selectedItems.length === 0) {
      this.groupedItems = [];
      return;
    }

    const grouped = new Map<number, GroupedCartItems>();

    this.selectedItems.forEach(item => {
      const shopId = item.variant_details.shop_id;
      const shopName = item.variant_details.shop_name;

      if (!grouped.has(shopId)) {
        grouped.set(shopId, {
          shop_id: shopId,
          shop_name: shopName,
          items: [],
          subtotal: 0
        });
      }

      const group = grouped.get(shopId)!;
      group.items.push(item);
      group.subtotal += parseFloat(item.price) * item.quantity;
    });

    this.groupedItems = Array.from(grouped.values());
  }

  calculateTotals(): void {
    this.totalProductAmount = this.selectedItems.reduce((sum, item) => {
      return sum + (parseFloat(item.price) * item.quantity);
    }, 0);

    this.totalAmount = this.totalProductAmount + this.shippingFee;
  }

  selectAddress(address: Address): void {
    this.selectedAddress = address;
  }

  goBack(): void {
    this.router.navigate(['/buyer/cart']);
  }

  goToAddressList(): void {
    // TODO: Implement address management page
    alert('Chức năng quản lý địa chỉ đang được phát triển');
  }

  placeOrder(): void {
    if (!this.selectedAddress) {
      alert('Vui lòng chọn địa chỉ giao hàng');
      return;
    }

    if (this.selectedItems.length === 0) {
      alert('Giỏ hàng trống');
      return;
    }

    const orderRequest: CreateOrderRequest = {
      address_id: this.selectedAddress.id,
      payment_method: this.paymentMethod,
      notes: this.orderNotes,
      cart_item_ids: this.selectedItems.map(item => item.id!).filter(id => id !== undefined)
    };

    this.loading = true;
    this.error = '';

    this.checkoutService.createOrder(orderRequest).subscribe({
      next: (response) => {
        if (response.success && response.data?.data) {
          const order = response.data.data;
          // Redirect to order success page with order details
          this.router.navigate(['/buyer/order-success'], {
            queryParams: {
              orderId: order.id,
              amount: order.total_amount
            }
          });
        }
        this.loading = false;
      },
      error: (err) => {
        console.error('Error creating order:', err);
        this.error = 'Không thể tạo đơn hàng. Vui lòng thử lại!';
        this.loading = false;
        alert(this.error);
      }
    });
  }

  formatPrice(price: string | number): string {
    const numPrice = typeof price === 'string' ? parseFloat(price) : price;
    return numPrice.toLocaleString('vi-VN') + '₫';
  }

  getFullAddress(address: Address): string {
    return `${address.street_address}, ${address.ward}, ${address.district}, ${address.province}`;
  }

  getPlaceholderImage(): string {
    return 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCIgZmlsbD0iI2YwZjBmMCIvPjx0ZXh0IHg9IjUwJSIgeT0iNTAlIiBmb250LWZhbWlseT0iQXJpYWwiIGZvbnQtc2l6ZT0iMTQiIGZpbGw9IiM5OTkiIHRleHQtYW5jaG9yPSJtaWRkbGUiIGR5PSIuM2VtIj5ObyBJbWFnZTwvdGV4dD48L3N2Zz4=';
  }

  onImageError(event: Event): void {
    const img = event.target as HTMLImageElement;
    img.src = this.getPlaceholderImage();
  }

  protected readonly parseFloat = parseFloat;
}

