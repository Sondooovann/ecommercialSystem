import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router } from '@angular/router';
import { OrderService } from '../../../core/services/order.service';
import { Order } from '../../../core/models/order.model';
import { SafeHtmlPipe } from '../../../shared/pipes/pipe-html.pipe';
import { ICON_BACK } from '../../../../assets/icons/icon';

interface OrderStatusInfo {
  label: string;
  color: string;
  icon: string;
  step: number;
}

interface CancellableInfo {
  order_id: number;
  current_status: string;
  status_display: string;
  is_cancellable: boolean;
  payment_status: string;
  cancellation_policy: string;
}

@Component({
  selector: 'jhi-order-detail',
  standalone: true,
  imports: [CommonModule, SafeHtmlPipe],
  templateUrl: './order-detail.component.html',
  styleUrls: ['./order-detail.component.scss']
})
export class OrderDetailComponent implements OnInit {
  order: Order | null = null;
  loading = false;
  error = '';

  cancellableInfo: CancellableInfo | null = null;
  showCancelDialog = false;

  protected readonly ICON_BACK = ICON_BACK;

  // SVG Icons
  readonly ICON_CLOCK = '<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>';
  readonly ICON_PROCESSING = '<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" /></svg>';
  readonly ICON_SHIPPED = '<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path d="M9 17a2 2 0 11-4 0 2 2 0 014 0zM19 17a2 2 0 11-4 0 2 2 0 014 0z" /><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16V6a1 1 0 00-1-1H4a1 1 0 00-1 1v10a1 1 0 001 1h1m8-1a1 1 0 01-1 1H9m4-1V8a1 1 0 011-1h2.586a1 1 0 01.707.293l3.414 3.414a1 1 0 01.293.707V16a1 1 0 01-1 1h-1m-6-1a1 1 0 001 1h1M5 17a2 2 0 104 0m-4 0a2 2 0 114 0m6 0a2 2 0 104 0m-4 0a2 2 0 114 0" /></svg>';
  readonly ICON_DELIVERED = '<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" /></svg>';
  readonly ICON_CANCELLED = '<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" /></svg>';
  readonly ICON_RETURNED = '<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 10h10a8 8 0 018 8v2M3 10l6 6m-6-6l6-6" /></svg>';

  orderStatusMap: { [key: string]: OrderStatusInfo } = {
    pending: {
      label: 'Chờ xác nhận',
      color: '#ff9800',
      icon: this.ICON_CLOCK,
      step: 0
    },
    processing: {
      label: 'Đang xử lý',
      color: '#2196f3',
      icon: this.ICON_PROCESSING,
      step: 1
    },
    shipped: {
      label: 'Đang giao',
      color: '#03a9f4',
      icon: this.ICON_SHIPPED,
      step: 2
    },
    delivered: {
      label: 'Đã giao',
      color: '#4caf50',
      icon: this.ICON_DELIVERED,
      step: 3
    },
    received: {
      label: 'Đã nhận hàng',
      color: '#4caf50',
      icon: this.ICON_DELIVERED,
      step: 4
    },
    received_reviewed: {
      label: 'Đã nhận hàng',
      color: '#4caf50',
      icon: this.ICON_DELIVERED,
      step: 4
    },
    cancelled: {
      label: 'Đã hủy',
      color: '#f44336',
      icon: this.ICON_CANCELLED,
      step: -1
    },
    returned: {
      label: 'Đã trả hàng',
      color: '#9e9e9e',
      icon: this.ICON_RETURNED,
      step: -1
    }
  };

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private orderService: OrderService
  ) {}

  ngOnInit(): void {
    const orderId = this.route.snapshot.paramMap.get('id');
    if (orderId) {
      this.loadOrderDetail(+orderId);
      this.checkCancellable(+orderId);
    }
  }

  loadOrderDetail(orderId: number): void {
    this.loading = true;
    this.error = '';

    this.orderService.getOrderById(orderId).subscribe({
      next: (response) => {
        if (response.success && response.data?.data) {
          this.order = response.data.data;
        }
        this.loading = false;
      },
      error: (err) => {
        console.error('Error loading order detail:', err);
        this.error = 'Không thể tải chi tiết đơn hàng';
        this.loading = false;
      }
    });
  }

  checkCancellable(orderId: number): void {
    this.orderService.checkCancellable(orderId).subscribe({
      next: (response) => {
        if (response.success && response.data?.data) {
          this.cancellableInfo = response.data.data;
        }
      },
      error: (err) => {
        console.error('Error checking cancellable:', err);
      }
    });
  }

  goBack(): void {
    this.router.navigate(['/buyer/orders']);
  }

  getStatusInfo(status: string): OrderStatusInfo {
    return this.orderStatusMap[status] || {
      label: status,
      color: '#757575',
      icon: this.ICON_CLOCK,
      step: 0
    };
  }

  getTrackingSteps(): Array<{ status: string; info: OrderStatusInfo; active: boolean; completed: boolean }> {
    if (!this.order) return [];

    const currentStatus = this.order.order_status;
    const currentStep = this.getStatusInfo(currentStatus).step;

    // Nếu đơn hàng bị hủy hoặc trả hàng, chỉ hiển thị các step đã qua và trạng thái hiện tại
    if (currentStep === -1) {
      return [
        { status: 'pending', info: this.orderStatusMap['pending'], active: false, completed: true },
        { status: currentStatus, info: this.getStatusInfo(currentStatus), active: true, completed: false }
      ];
    }

    // Các step bình thường
    const normalSteps = ['pending', 'processing', 'shipped', 'delivered', 'received'];

    return normalSteps.map((status, index) => ({
      status,
      info: this.orderStatusMap[status],
      active: index === currentStep,
      completed: index < currentStep
    }));
  }

  openCancelDialog(): void {
    this.showCancelDialog = true;
  }

  closeCancelDialog(): void {
    this.showCancelDialog = false;
  }

  confirmCancel(): void {
    if (!this.order) return;

    if (confirm('Bạn có chắc chắn muốn hủy đơn hàng này?')) {
      this.orderService.cancelOrder(this.order.id).subscribe({
        next: (response) => {
          if (response.success) {
            alert('Đã hủy đơn hàng thành công');
            this.loadOrderDetail(this.order!.id);
            this.checkCancellable(this.order!.id);
            this.closeCancelDialog();
          }
        },
        error: (err) => {
          console.error('Error cancelling order:', err);
          alert('Không thể hủy đơn hàng. Vui lòng thử lại sau.');
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

  getFullAddress(): string {
    if (!this.order?.address) return '';
    const addr = this.order.address;
    return `${addr.street_address}, ${addr.ward}, ${addr.district}, ${addr.province}`;
  }

  getPaymentMethodText(method: string): string {
    const methodMap: { [key: string]: string } = {
      'cod': 'Thanh toán khi nhận hàng (COD)',
      'online': 'Thanh toán online',
      'e_wallet': 'Ví điện tử'
    };
    return methodMap[method] || method;
  }

  getPaymentStatusText(status: string): string {
    const statusMap: { [key: string]: string } = {
      'pending': 'Chờ thanh toán',
      'success': 'Đã thanh toán',
      'failed': 'Thanh toán thất bại'
    };
    return statusMap[status] || status;
  }

  getVariantText(variantDetails: any): string {
    if (!variantDetails?.attributes || variantDetails.attributes.length === 0) {
      return 'Không có biến thể';
    }
    return variantDetails.attributes
      .map((attr: any) => `${attr.display_name}: ${attr.display_value}`)
      .join(', ');
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

