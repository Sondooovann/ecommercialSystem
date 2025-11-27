import {Injectable} from '@angular/core';
import {BehaviorSubject, map, Observable, tap} from 'rxjs';
import {
  LoginRequest,
  User,
  LoginResponse,
  UserRegistrationRequest,
  UserRegistrationResponse, UserRole
} from '../models/user.model';
import {HttpClient} from '@angular/common/http';
import {environment} from '../../../environments/environment';
import {LOGIN, REGISTER} from '../../constants/url.constant';
import {StorageService} from './storage.service';
import {Router} from '@angular/router';
import {ApiResponse} from '../models/api-response.model';

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private currentUserSubject = new BehaviorSubject(<User | null>(null));
  public currentUser$ = this.currentUserSubject.asObservable();

  constructor(
    private http: HttpClient,
    private storageService: StorageService,
    private router: Router,
  ) {
    const user = this.storageService.getItem<User>(environment.userKey);
    if (user) {
      this.currentUserSubject.next(user);
    }
  }

  login(credentials: LoginRequest): Observable<LoginResponse> {
    return this.http.post<ApiResponse<LoginResponse>>(
      `${environment.apiUrl}${LOGIN}`,
      credentials
    ).pipe(
      map(response => {
        if (response.success && response.data) {
          this.storageService.setItem(environment.userKey, response.data.user);
          this.storageService.setItem(environment.tokenKey, response.data.access);
          // @ts-ignore
          this.currentUserSubject.next(response.data.user);
          return response.data;
        }
        throw new Error(response.message || 'Đăng nhập thất bại');
      })
    );
  }


  register(data: UserRegistrationRequest): Observable<UserRegistrationResponse> {
    return this.http.post<ApiResponse<UserRegistrationResponse>>(
      `${environment.apiUrl}${REGISTER}`,
      data
    ).pipe(
      map(response => {
        if (response.success && response.data) {
          return response.data;
        }
        throw new Error(response.message || 'Đăng ký thất bại');
      })
    );
  }

  verifyOtp(data: { email: string; otp_code: string }): Observable<any> {
    return this.http.post<ApiResponse<any>>(
      `${environment.apiUrl}/api/users/verify-otp/`,
      data
    ).pipe(
      map(response => {
        if (response.success) {
          return response.data;
        }
        throw new Error(response.message || 'Xác thực OTP thất bại');
      })
    );
  }

  resendOtp(email: string): Observable<any> {
    return this.http.post<ApiResponse<any>>(
      `${environment.apiUrl}/api/users/resend-otp/`,
      { email }
    ).pipe(
      map(response => {
        if (response.success) {
          return response.data;
        }
        throw new Error(response.message || 'Gửi lại OTP thất bại');
      })
    );
  }

  logout(): void{
    this.storageService.clear();
    this.currentUserSubject.next(null);
    this.router.navigate(['/login']);
  }

  getToken(): string | null {
    return this.storageService.getItem<string>(environment.tokenKey);
  }

  getCurrentUser(): User | null {
    return this.currentUserSubject.value;
  }

  isAuthenticated(): boolean {
    return !!this.getToken();
  }

  hasRole(role: UserRole): boolean {
    const user = this.getCurrentUser();
    return user?.role === role;
  }
}
