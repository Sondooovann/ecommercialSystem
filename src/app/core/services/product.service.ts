import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable, map } from 'rxjs';
import { environment } from '../../../environments/environment';
import { ApiResponse } from '../models/api-response.model';
import {
  Product,
  ProductApiResponse,
  ProductDetail,
  ProductDetailResponse,
  ProductListResponse
} from '../models/product.model';

@Injectable({
  providedIn: 'root'
})
export class ProductService {
  constructor(private http: HttpClient) {}

  getProductDetail(productId: number) : Observable<any> {
    return this.http.get<ApiResponse<ProductDetailResponse>>(`${environment.apiUrl}/api/products/${productId}/`)
      .pipe(
        map(response => {
          if(response.success && response.data){
            return response.data.data;
          }
          throw new Error(response.message || 'Lấy danh sách sản phẩm thất bại');
        })
      )
  }

  getProductsByShop(
    shopId: number,
    page: number = 1,
    pageSize: number = 10,
    filters?: {
      status?: string;
      category_id?: number;
      search?: string;
      sort_by?: string;
      sort_order?: string;
    }
  ): Observable<ProductListResponse> {
    let params = new HttpParams()
      .set('page', page.toString())
      .set('page_size', pageSize.toString());

    // Thêm các filter nếu có
    if (filters) {
      if (filters.status) {
        params = params.set('status', filters.status);
      }
      if (filters.category_id) {
        params = params.set('category_id', filters.category_id.toString());
      }
      if (filters.search) {
        params = params.set('search', filters.search);
      }
      if (filters.sort_by) {
        params = params.set('sort_by', filters.sort_by);
      }
      if (filters.sort_order) {
        params = params.set('sort_order', filters.sort_order);
      }
    }

    return this.http
      .get<ApiResponse<ProductApiResponse>>(
        `${environment.apiUrl}/api/products/shops/${shopId}/products/`,
        { params }
      )
      .pipe(
        map(response => {
          if (response.success && response.data) {
            return response.data.data;
          }
          throw new Error(response.message || 'Lấy danh sách sản phẩm thất bại');
        })
      );
  }

  getProductsByCategory(
    categoryId: number,
    page: number = 1,
    pageSize: number = 20,
    sortBy: string = 'latest'
  ): Observable<ProductListResponse> {
    let params = new HttpParams()
      .set('page', page.toString())
      .set('page_size', pageSize.toString())
      .set('category_id', categoryId.toString())
      .set('sort_by', sortBy);

    return this.http
      .get<ApiResponse<ProductApiResponse>>(
        `${environment.apiUrl}/api/products/products/by-category/`,
        { params }
      )
      .pipe(
        map(response => {
          if (response.success && response.data) {
            return response.data.data;
          }
          throw new Error(response.message || 'Lấy danh sách sản phẩm theo danh mục thất bại');
        })
      );
  }

  getTopSellingProducts(): Observable<TopSellingProduct[]> {
    return this.http
      .get<ApiResponse<TopSellingProduct[]>>(`${environment.apiUrl}/api/products/top-selling/`)
      .pipe(
        map(response => {
          if (response.success && response.data) {
            return response.data;
          }
          throw new Error(response.message || 'Lấy danh sách sản phẩm bán chạy thất bại');
        })
      );
  }

  createProduct(shopId: number, formData: FormData): Observable<any> {
    return this.http.post<ApiResponse<any>>(
      `${environment.apiUrl}/api/products/shops/${shopId}/products/`,
      formData
    );
  }

  updateProduct(shopId: number, productId: number, formData: FormData): Observable<any> {
    return this.http.put<ApiResponse<any>>(
      `${environment.apiUrl}/api/products/shops/${shopId}/products/${productId}/`,
      formData
    );
  }
}

export interface TopSellingProduct {
  id: number;
  name: string;
  total_sold: number;
}

