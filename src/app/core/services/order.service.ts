import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';
import { ApiResponse } from '../models/api-response.model';
import { Order, OrderSummary } from '../models/order.model';

export interface OrderListResponse {
  orders: OrderSummary[];
  pagination: {
    total: number;
    page: number;
    page_size: number;
    total_pages: number;
  };
}

@Injectable({
  providedIn: 'root'
})
export class OrderService {
  private apiUrl = environment.apiUrl;

  constructor(private http: HttpClient) {}

  /**
   * Lấy danh sách đơn hàng của người dùng
   */
  getOrders(page: number = 1, pageSize: number = 10, status?: string): Observable<ApiResponse<{ status: string; message: string; data: OrderListResponse }>> {
    let params = new HttpParams()
      .set('page', page.toString())
      .set('page_size', pageSize.toString());

    if (status) {
      params = params.set('status', status);
    }

    return this.http.get<ApiResponse<{ status: string; message: string; data: OrderListResponse }>>(
      `${this.apiUrl}/api/orders/`,
      { params }
    );
  }

  /**
   * Lấy chi tiết một đơn hàng
   */
  getOrderById(orderId: number): Observable<ApiResponse<{ status: string; message: string; data: Order }>> {
    return this.http.get<ApiResponse<{ status: string; message: string; data: Order }>>(
      `${this.apiUrl}/api/orders/${orderId}/`
    );
  }

  /**
   * Kiểm tra đơn hàng có thể hủy không
   */
  checkCancellable(orderId: number): Observable<ApiResponse<any>> {
    return this.http.get<ApiResponse<any>>(
      `${this.apiUrl}/api/orders/${orderId}/check-cancellable/`
    );
  }

  /**
   * Hủy đơn hàng
   */
  cancelOrder(orderId: number, reason?: string): Observable<ApiResponse<any>> {
    return this.http.post<ApiResponse<any>>(
      `${this.apiUrl}/api/orders/${orderId}/cancel/`,
      { reason }
    );
  }

  /**
   * Lấy danh sách tất cả đơn hàng (Admin)
   */
  getAdminOrders(
    page: number = 1,
    pageSize: number = 10,
    filters?: {
      status?: string;
      search?: string;
      start_date?: string;
      end_date?: string;
      user_id?: string;
      payment_status?: string;
      order_by?: string;
    }
  ): Observable<ApiResponse<{ status: string; message: string; data: OrderListResponse }>> {
    let params = new HttpParams()
      .set('page', page.toString())
      .set('page_size', pageSize.toString());

    if (filters) {
      if (filters.status) params = params.set('status', filters.status);
      if (filters.search) params = params.set('search', filters.search);
      if (filters.start_date) params = params.set('start_date', filters.start_date);
      if (filters.end_date) params = params.set('end_date', filters.end_date);
      if (filters.user_id) params = params.set('user_id', filters.user_id);
      if (filters.payment_status) params = params.set('payment_status', filters.payment_status);
      if (filters.order_by) params = params.set('order_by', filters.order_by);
    }

    return this.http.get<ApiResponse<{ status: string; message: string; data: OrderListResponse }>>(
      `${this.apiUrl}/api/orders/admin/orders/`,
      { params }
    );
  }

  /**
   * Cập nhật trạng thái đơn hàng (Admin)
   */
  updateOrderStatus(orderId: number, status: string, note?: string): Observable<ApiResponse<any>> {
    return this.http.post<ApiResponse<any>>(
      `${this.apiUrl}/api/orders/admin/orders/${orderId}/update-status/`,
      { status, note }
    );
  }

  /**
   * Cập nhật trạng thái đơn hàng hàng loạt (Admin)
   */
  bulkUpdateOrderStatus(orderIds: number[], status: string, note?: string): Observable<ApiResponse<any>> {
    return this.http.post<ApiResponse<any>>(
      `${this.apiUrl}/api/orders/bulk-update-status/`,
      { order_ids: orderIds, status, note }
    );
  }
}

