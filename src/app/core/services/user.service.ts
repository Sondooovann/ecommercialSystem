import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';
import { ApiResponse } from '../models/api-response.model';
import { User } from '../models/user.model';

export interface UserListResponse {
  users: User[];
  pagination: {
    total: number;
    pages: number;
    current_page: number;
    page_size: number;
  };
}

@Injectable({
  providedIn: 'root'
})
export class UserService {
  private apiUrl = environment.apiUrl;

  constructor(private http: HttpClient) {}

  /**
   * Lấy danh sách người dùng (Admin)
   */
  getAdminUsers(
    page: number = 1,
    pageSize: number = 10,
    filters?: {
      status?: string;
      search?: string;
      role?: string;
    }
  ): Observable<ApiResponse<{ status: string; message: string; data: UserListResponse }>> {
    let params = new HttpParams()
      .set('page', page.toString())
      .set('page_size', pageSize.toString());

    if (filters) {
      if (filters.status) params = params.set('status', filters.status);
      if (filters.search) params = params.set('search', filters.search);
      if (filters.role) params = params.set('role', filters.role);
    }

    return this.http.get<ApiResponse<{ status: string; message: string; data: UserListResponse }>>(
      `${this.apiUrl}/api/users/admin/users/`,
      { params }
    );
  }

  /**
   * Lấy chi tiết người dùng (Admin)
   */
  getUserById(userId: number): Observable<ApiResponse<{ status: string; message: string; data: User }>> {
    return this.http.get<ApiResponse<{ status: string; message: string; data: User }>>(
      `${this.apiUrl}/api/users/admin/users/${userId}/`
    );
  }

  /**
   * Cập nhật thông tin người dùng (Admin)
   */
  updateUser(userId: number, userData: Partial<User>): Observable<ApiResponse<any>> {
    return this.http.put<ApiResponse<any>>(
      `${this.apiUrl}/api/users/admin/users/${userId}/`,
      userData
    );
  }

  /**
   * Cập nhật trạng thái người dùng (Admin)
   */
  updateUserStatus(userId: number, status: string): Observable<ApiResponse<any>> {
    return this.http.patch<ApiResponse<any>>(
      `${this.apiUrl}/api/users/admin/users/${userId}/status/`,
      { status }
    );
  }

  /**
   * Xóa người dùng (Admin)
   */
  deleteUser(userId: number): Observable<ApiResponse<any>> {
    return this.http.delete<ApiResponse<any>>(
      `${this.apiUrl}/api/users/admin/users/${userId}/`
    );
  }
}

