import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { SafeHtmlPipe } from '../../../shared/pipes/pipe-html.pipe';

interface StatCard {
  title: string;
  value: string | number;
  icon: string;
  color: string;
  change?: string;
  changeType?: 'up' | 'down';
}

interface RecentOrder {
  id: number;
  customerName: string;
  total: number;
  status: string;
  date: string;
}

@Component({
  selector: 'jhi-dashboard',
  standalone: true,
  imports: [CommonModule, SafeHtmlPipe],
  templateUrl: './dashboard.component.html',
  styleUrls: ['./dashboard.component.scss']
})
export class DashboardComponent implements OnInit {
  loading = false;

  // SVG Icons
  readonly ICON_REVENUE = '<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>';
  readonly ICON_ORDERS = '<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z" /></svg>';
  readonly ICON_PRODUCTS = '<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" /></svg>';
  readonly ICON_USERS = '<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" /></svg>';
  readonly ICON_ARROW_UP = '<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" /></svg>';
  readonly ICON_ARROW_DOWN = '<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 17h8m0 0V9m0 8l-8-8-4 4-6-6" /></svg>';

  statCards: StatCard[] = [
    {
      title: 'Doanh thu tháng này',
      value: '125,000,000₫',
      icon: this.ICON_REVENUE,
      color: '#4caf50',
      change: '+12.5%',
      changeType: 'up'
    },
    {
      title: 'Đơn hàng',
      value: 234,
      icon: this.ICON_ORDERS,
      color: '#2196f3',
      change: '+8.2%',
      changeType: 'up'
    },
    {
      title: 'Sản phẩm',
      value: 156,
      icon: this.ICON_PRODUCTS,
      color: '#ff9800',
      change: '+3',
      changeType: 'up'
    },
    {
      title: 'Khách hàng',
      value: 1024,
      icon: this.ICON_USERS,
      color: '#9c27b0',
      change: '+15.3%',
      changeType: 'up'
    }
  ];

  recentOrders: RecentOrder[] = [
    { id: 19, customerName: 'Vu Thi Xinh', total: 120000, status: 'pending', date: '2025-11-07T18:55:34' },
    { id: 18, customerName: 'Vu Thi Xinh', total: 210000, status: 'pending', date: '2025-11-07T18:48:08' },
    { id: 17, customerName: 'Vu Thi Xinh', total: 210000, status: 'pending', date: '2025-11-07T18:35:00' },
    { id: 16, customerName: 'Vu Thi Xinh', total: 750000, status: 'cancelled', date: '2025-05-20T08:52:33' },
    { id: 15, customerName: 'Vu Thi Xinh', total: 120000, status: 'cancelled', date: '2025-05-20T08:43:51' }
  ];

  constructor(private router: Router) {}

  ngOnInit(): void {
    this.loadDashboardData();
  }

  loadDashboardData(): void {
    this.loading = true;
    // TODO: Call API to get real dashboard data
    setTimeout(() => {
      this.loading = false;
    }, 500);
  }

  navigateToProducts(): void {
    this.router.navigate(['/admin/products']);
  }

  navigateToOrders(): void {
    this.router.navigate(['/admin/orders']);
  }

  navigateToUsers(): void {
    this.router.navigate(['/admin/users']);
  }

  navigateToReports(): void {
    this.router.navigate(['/admin/reports']);
  }

  viewOrderDetail(orderId: number): void {
    this.router.navigate(['/admin/orders', orderId]);
  }

  formatPrice(price: number): string {
    return price.toLocaleString('vi-VN') + '₫';
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
}

