import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { OrderService } from '../../../core/services/order.service';
import { OrderSummary } from '../../../core/models/order.model';
import { SafeHtmlPipe } from '../../../shared/pipes/pipe-html.pipe';
import { ICON_BACK } from '../../../../assets/icons/icon';

@Component({
  selector: 'jhi-order-list',
  standalone: true,
  imports: [CommonModule, SafeHtmlPipe],
  templateUrl: './order-list.component.html',
  styleUrls: ['./order-list.component.scss']
})
export class OrderListComponent implements OnInit {
  orders: OrderSummary[] = [];
  loading = false;
  error = '';
  
  currentPage = 1;
  pageSize = 10;
  totalOrders = 0;
  totalPages = 1;

  selectedTab: 'all' | 'pending' | 'processing' | 'shipped' | 'delivered' | 'cancelled' = 'all';

  protected readonly ICON_BACK = ICON_BACK;

  constructor(
    private orderService: OrderService,
    private router: Router
  ) {}

  ngOnInit(): void {
    this.loadOrders();
  }

  loadOrders(): void {
    this.loading = true;
    this.error = '';

    const status = this.selectedTab === 'all' ? undefined : this.selectedTab;

    this.orderService.getOrders(this.currentPage, this.pageSize, status).subscribe({
      next: (response) => {
        if (response.success && response.data?.data) {
          this.orders = response.data.data.orders || [];
          const pagination = response.data.data.pagination;
          this.totalOrders = pagination?.total || 0;
          this.totalPages = pagination?.total_pages || 1;
          this.currentPage = pagination?.page || 1;
        }
        this.loading = false;
      },
      error: (err) => {
        console.error('Error loading orders:', err);
        this.error = 'Không thể tải danh sách đơn hàng';
        this.loading = false;
      }
    });
  }

  selectTab(tab: typeof this.selectedTab): void {
    this.selectedTab = tab;
    this.currentPage = 1;
    this.loadOrders();
  }

  onPageChange(page: number): void {
    if (page >= 1 && page <= this.totalPages) {
      this.currentPage = page;
      this.loadOrders();
    }
  }

  goBack(): void {
    this.router.navigate(['/buyer/home']);
  }

  viewOrderDetail(orderId: number): void {
    this.router.navigate(['/buyer/orders', orderId]);
  }

  formatPrice(price: string | number): string {
    const numPrice = typeof price === 'string' ? parseFloat(price) : price;
    return numPrice.toLocaleString('vi-VN') + '₫';
  }

  formatDate(dateString: string): string {
    const date = new Date(dateString);
    return date.toLocaleDateString('vi-VN', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  }

  getStatusText(status: string): string {
    const statusMap: { [key: string]: string } = {
      'pending': 'Chờ xác nhận',
      'processing': 'Đang xử lý',
      'shipped': 'Đang giao',
      'delivered': 'Đã giao',
      'cancelled': 'Đã hủy',
      'received_reviewed': 'Đã nhận & Đánh giá'
    };
    return statusMap[status] || status;
  }

  getStatusClass(status: string): string {
    return `status-${status}`;
  }

  getPlaceholderImage(): string {
    return 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCIgZmlsbD0iI2YwZjBmMCIvPjx0ZXh0IHg9IjUwJSIgeT0iNTAlIiBmb250LWZhbWlseT0iQXJpYWwiIGZvbnQtc2l6ZT0iMTQiIGZpbGw9IiM5OTkiIHRleHQtYW5jaG9yPSJtaWRkbGUiIGR5PSIuM2VtIj5ObyBJbWFnZTwvdGV4dD48L3N2Zz4=';
  }

  onImageError(event: Event): void {
    const img = event.target as HTMLImageElement;
    img.src = this.getPlaceholderImage();
  }
}

