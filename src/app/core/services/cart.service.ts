import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, BehaviorSubject } from 'rxjs';
import { tap } from 'rxjs/operators';
import { environment } from '../../../environments/environment';
import { Cart, CartResponse } from '../models/cart.model';

@Injectable({
  providedIn: 'root'
})
export class CartService {
  private apiUrl = `${environment.apiUrl}/api/cart`;
  private cartSubject = new BehaviorSubject<Cart | null>(null);
  public cart$ = this.cartSubject.asObservable();

  constructor(private http: HttpClient) {}

  getCart(): Observable<CartResponse> {
    return this.http.get<CartResponse>(`${this.apiUrl}/`).pipe(
      tap(response => {
        if (response.success && response.data?.data) {
          this.cartSubject.next(response.data.data);
        }
      })
    );
  }

  addToCart(productId: number, quantity: number): Observable<any> {
    return this.http.post(`${this.apiUrl}/add/`, { product_id: productId, quantity });
  }

  addToCartWithVariant(variantId: number | null, quantity: number): Observable<any> {
    const cartData = {
      variant_id: variantId,
      quantity: quantity
    };
    return this.http.post(`${this.apiUrl}/`, cartData).pipe(
      tap(() => {
        // Refresh cart after adding item
        this.getCart().subscribe();
      })
    );
  }

  updateCartItem(itemId: number, quantity: number): Observable<any> {
    return this.http.put(`${this.apiUrl}/update/${itemId}/`, { quantity });
  }

  removeFromCart(itemId: number): Observable<any> {
    return this.http.delete(`${this.apiUrl}/remove/${itemId}/`);
  }

  clearCart(): Observable<any> {
    return this.http.delete(`${this.apiUrl}/clear/`);
  }
}


