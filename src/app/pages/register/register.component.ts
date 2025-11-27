import { Component } from '@angular/core';
import { FormControl, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import {
  ICON_EYE_LINEAR,
  ICON_EYE_SLASH_LINEAR,
  ICON_LOCATION_DOT,
  ICON_LOCK_LINEAR,
  ICON_MAIL_REGULAR,
  ICON_PHONE_SOLID,
  ICON_USER_LINEAR
} from '../../../assets/icons/icon';
import { SafeHtmlPipe } from '../../shared/pipes/pipe-html.pipe';
import { Router } from '@angular/router';
import { AuthService } from '../../core/services/auth.service';
import { NotificationService } from '../../core/services/notification.service';
import { catchError, of } from 'rxjs';
import { UserRegistrationRequest } from '../../core/models/user.model';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'jhi-register',
  standalone: true,
  templateUrl: './register.component.html',
  imports: [
    CommonModule,
    ReactiveFormsModule,
    SafeHtmlPipe
  ],
  styleUrls: ['./register.component.scss', './../../../styles/scss/global.scss'],
})
export class RegisterComponent {
  passwordVisible: boolean = false;
  confirmPasswordVisible: boolean = false;
  loading = false;

  registerForm = new FormGroup({
    email: new FormControl('', [Validators.required, Validators.email]),
    full_name: new FormControl('', Validators.required),
    phone: new FormControl('', [Validators.required, Validators.pattern(/^[0-9]{10,11}$/)]),
    password: new FormControl('', [Validators.required, Validators.minLength(6)]),
    confirm_password: new FormControl('', Validators.required),
    role: new FormControl('customer')
  }, { validators: this.passwordMatchValidator });

  constructor(
    private authService: AuthService,
    private router: Router,
    private notificationService: NotificationService
  ) {}

  passwordMatchValidator(control: any) {
    const password = control.get('password');
    const confirmPassword = control.get('confirm_password');
    
    if (!password || !confirmPassword) {
      return null;
    }

    return password.value === confirmPassword.value ? null : { passwordMismatch: true };
  }

  showPassword(event: Event) {
    event.preventDefault();
    event.stopPropagation();
    this.passwordVisible = !this.passwordVisible;
  }

  showConfirmPassword(event: Event) {
    event.preventDefault();
    event.stopPropagation();
    this.confirmPasswordVisible = !this.confirmPasswordVisible;
  }

  register() {
    if (this.registerForm.invalid) {
      if (this.registerForm.hasError('passwordMismatch')) {
        this.notificationService.warning('Mật khẩu xác nhận không khớp.');
      } else {
        this.notificationService.warning('Vui lòng nhập đầy đủ và chính xác thông tin đăng ký.');
      }
      this.registerForm.markAllAsTouched();
      return;
    }

    this.loading = true;

    this.authService.register(this.registerForm.value as UserRegistrationRequest).pipe(
      catchError(err => {
        const errorMsg = err.error?.message || 'Đăng ký thất bại. Vui lòng thử lại.';
        this.notificationService.error(errorMsg);
        this.loading = false;
        return of(null);
      })
    ).subscribe(response => {
      this.loading = false;
      if (response) {
        this.notificationService.success('Đăng ký thành công! Vui lòng kiểm tra email để nhận mã OTP.');
        setTimeout(() => {
          // Navigate to verify OTP page with email
          this.router.navigate(['/verify-otp'], { 
            queryParams: { email: this.registerForm.value.email } 
          });
        }, 2000);
      }
    });
  }

  protected readonly LOGIN_ROUTE = '/login';
  protected readonly ICON_USER = ICON_USER_LINEAR;
  protected readonly ICON_LOCK = ICON_LOCK_LINEAR;
  protected readonly ICON_EYE = ICON_EYE_LINEAR;
  protected readonly ICON_EYE_SLASH = ICON_EYE_SLASH_LINEAR;
  protected readonly ICON_LOCATION = ICON_LOCATION_DOT;
  protected readonly ICON_MAIL = ICON_MAIL_REGULAR;
  protected readonly ICON_PHONE = ICON_PHONE_SOLID;
}

