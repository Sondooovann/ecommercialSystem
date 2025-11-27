import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';
import { ApiResponse } from '../models/api-response.model';
import { Address, AddressListResponse } from '../models/address.model';
import { CreateOrderRequest, CreateOrderResponse } from '../models/order.model';

@Injectable({
  providedIn: 'root'
})
export class CheckoutService {
  private apiUrl = environment.apiUrl + '/api';

  constructor(private http: HttpClient) {}

  /**
   * Lấy danh sách địa chỉ của người dùng
   */
  getAddresses(): Observable<ApiResponse<{ status: string; message: string; data: AddressListResponse }>> {
    return this.http.get<ApiResponse<{ status: string; message: string; data: AddressListResponse }>>(
      `${this.apiUrl}/users/addresses/`
    );
  }

  /**
   * Tạo đơn hàng mới
   */
  createOrder(request: CreateOrderRequest): Observable<ApiResponse<{ status: string; message: string; data: CreateOrderResponse }>> {
    return this.http.post<ApiResponse<{ status: string; message: string; data: CreateOrderResponse }>>(
      `${this.apiUrl}/orders/create/`,
      request
    );
  }

  /**
   * Thêm địa chỉ mới
   */
  addAddress(address: Partial<Address>): Observable<ApiResponse<any>> {
    return this.http.post<ApiResponse<any>>(
      `${this.apiUrl}/users/addresses/`,
      address
    );
  }

  /**
   * Cập nhật địa chỉ
   */
  updateAddress(id: number, address: Partial<Address>): Observable<ApiResponse<any>> {
    return this.http.put<ApiResponse<any>>(
      `${this.apiUrl}/users/addresses/${id}/`,
      address
    );
  }

  /**
   * Xóa địa chỉ
   */
  deleteAddress(id: number): Observable<ApiResponse<any>> {
    return this.http.delete<ApiResponse<any>>(
      `${this.apiUrl}/users/addresses/${id}/`
    );
  }
}

