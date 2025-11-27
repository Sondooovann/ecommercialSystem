import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { OrderService } from '../../../../core/services/order.service';
import { OrderSummary } from '../../../../core/models/order.model';
import { SafeHtmlPipe } from '../../../../shared/pipes/pipe-html.pipe';
import {ICON_SEARCH, ICON_VIEW} from '../../../../../assets/icons/icon';

@Component({
  selector: 'jhi-admin-order-list',
  standalone: true,
  imports: [CommonModule, FormsModule, SafeHtmlPipe],
  templateUrl: './admin-order-list.component.html',
  styleUrls: ['./admin-order-list.component.scss']
})
export class AdminOrderListComponent implements OnInit {
  orders: OrderSummary[] = [];
  loading = false;
  error = '';

  // Filters
  selectedTab: 'all' | 'pending' | 'processing' | 'shipped' | 'delivered' | 'cancelled' | 'received_reviewed' = 'all';
  searchText = '';
  selectedPaymentStatus: 'all' | 'pending' | 'success' = 'all';
  startDate = '';
  endDate = '';

  // Pagination
  currentPage = 1;
  pageSize = 10;
  totalOrders = 0;
  totalPages = 1;

  // Bulk actions
  selectedOrderIds: number[] = [];
  bulkStatus: string = '';
  bulkNote: string = '';
  showBulkModal = false;

  // SVG Icons
  readonly ICON_SEARCH = ICON_SEARCH;
  readonly ICON_FILTER = '<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" /></svg>';
  readonly ICON_VIEW = ICON_VIEW;
  tabStats = {
    all: 0,
    pending: 0,
    processing: 0,
    shipped: 0,
    delivered: 0,
    cancelled: 0
  };

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

    const filters: any = {};

    if (this.selectedTab !== 'all') {
      filters.status = this.selectedTab;
    }

    if (this.searchText.trim()) {
      filters.search = this.searchText.trim();
    }

    if (this.selectedPaymentStatus !== 'all') {
      filters.payment_status = this.selectedPaymentStatus;
    }

    if (this.startDate) {
      filters.start_date = this.startDate;
    }

    if (this.endDate) {
      filters.end_date = this.endDate;
    }

    this.orderService.getAdminOrders(this.currentPage, this.pageSize, filters).subscribe({
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

  onSearch(): void {
    this.currentPage = 1;
    this.loadOrders();
  }

  onPageChange(page: number): void {
    if (page >= 1 && page <= this.totalPages) {
      this.currentPage = page;
      this.loadOrders();
    }
  }

  viewOrderDetail(orderId: number): void {
    this.router.navigate(['/admin/orders', orderId]);
  }

  updateOrderStatus(order: OrderSummary, newStatus: string): void {
    if (confirm(`Bạn có chắc chắn muốn cập nhật trạng thái đơn hàng #${order.id} thành "${this.getStatusText(newStatus)}"?`)) {
      this.orderService.updateOrderStatus(order.id, newStatus).subscribe({
        next: (response) => {
          if (response.success) {
            alert('Cập nhật trạng thái đơn hàng thành công!');
            this.loadOrders();
          }
        },
        error: (err) => {
          console.error('Error updating order status:', err);
          alert('Không thể cập nhật trạng thái đơn hàng');
        }
      });
    }
  }

  onFilterChange(): void {
    this.currentPage = 1;
    this.loadOrders();
  }

  clearFilters(): void {
    this.selectedTab = 'all';
    this.searchText = '';
    this.selectedPaymentStatus = 'all';
    this.startDate = '';
    this.endDate = '';
    this.currentPage = 1;
    this.loadOrders();
  }

  toggleOrderSelection(orderId: number): void {
    const index = this.selectedOrderIds.indexOf(orderId);
    if (index > -1) {
      this.selectedOrderIds.splice(index, 1);
    } else {
      this.selectedOrderIds.push(orderId);
    }
  }

  toggleSelectAll(event: Event): void {
    const checkbox = event.target as HTMLInputElement;
    if (checkbox.checked) {
      this.selectedOrderIds = this.orders.map(order => order.id);
    } else {
      this.selectedOrderIds = [];
    }
  }

  isOrderSelected(orderId: number): boolean {
    return this.selectedOrderIds.includes(orderId);
  }

  get isAllSelected(): boolean {
    return this.orders.length > 0 && this.selectedOrderIds.length === this.orders.length;
  }

  openBulkUpdateModal(): void {
    if (this.selectedOrderIds.length === 0) {
      alert('Vui lòng chọn ít nhất một đơn hàng');
      return;
    }
    this.bulkStatus = '';
    this.bulkNote = '';
    this.showBulkModal = true;
  }

  closeBulkModal(): void {
    this.showBulkModal = false;
    this.bulkStatus = '';
    this.bulkNote = '';
  }

  bulkUpdateStatus(): void {
    if (!this.bulkStatus) {
      alert('Vui lòng chọn trạng thái');
      return;
    }

    if (confirm(`Bạn có chắc chắn muốn cập nhật ${this.selectedOrderIds.length} đơn hàng sang trạng thái "${this.getStatusText(this.bulkStatus)}"?`)) {
      this.orderService.bulkUpdateOrderStatus(this.selectedOrderIds, this.bulkStatus, this.bulkNote).subscribe({
        next: (response) => {
          if (response.success) {
            alert('Cập nhật trạng thái hàng loạt thành công!');
            this.selectedOrderIds = [];
            this.closeBulkModal();
            this.loadOrders();
          }
        },
        error: (err) => {
          console.error('Error bulk updating order status:', err);
          alert('Không thể cập nhật trạng thái đơn hàng');
        }
      });
    }
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

  getPaymentMethodText(method: string): string {
    const methodMap: { [key: string]: string } = {
      'cod': 'COD',
      'online': 'Online',
      'e_wallet': 'Ví điện tử'
    };
    return methodMap[method] || method;
  }

  getPaymentStatusClass(status: string): string {
    return `payment-${status}`;
  }

  getPlaceholderImage(): string {
    return 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCIgZmlsbD0iI2YwZjBmMCIvPjx0ZXh0IHg9IjUwJSIgeT0iNTAlIiBmb250LWZhbWlseT0iQXJpYWwiIGZvbnQtc2l6ZT0iMTQiIGZpbGw9IiM5OTkiIHRleHQtYW5jaG9yPSJtaWRkbGUiIGR5PSIuM2VtIj5ObyBJbWFnZTwvdGV4dD48L3N2Zz4=';
  }

  onImageError(event: Event): void {
    const img = event.target as HTMLImageElement;
    img.src = this.getPlaceholderImage();
  }
}

