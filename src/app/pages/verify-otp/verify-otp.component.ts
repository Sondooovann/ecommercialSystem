import { Component, OnInit } from '@angular/core';
import { FormControl, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import {
  ICON_LOCATION_DOT,
  ICON_MAIL_REGULAR,
  ICON_PHONE_SOLID
} from '../../../assets/icons/icon';
import { SafeHtmlPipe } from '../../shared/pipes/pipe-html.pipe';
import { ActivatedRoute, Router } from '@angular/router';
import { AuthService } from '../../core/services/auth.service';
import { NotificationService } from '../../core/services/notification.service';
import { catchError, of } from 'rxjs';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'jhi-verify-otp',
  standalone: true,
  templateUrl: './verify-otp.component.html',
  imports: [
    CommonModule,
    ReactiveFormsModule,
    SafeHtmlPipe
  ],
  styleUrls: ['./verify-otp.component.scss', './../../../styles/scss/global.scss'],
})
export class VerifyOtpComponent implements OnInit {
  loading = false;
  email = '';

  otpForm = new FormGroup({
    email: new FormControl('', [Validators.required, Validators.email]),
    otp_code: new FormControl('', [Validators.required, Validators.minLength(6), Validators.maxLength(6)])
  });

  constructor(
    private authService: AuthService,
    private router: Router,
    private route: ActivatedRoute,
    private notificationService: NotificationService
  ) {}

  ngOnInit(): void {
    // Get email from query params
    this.route.queryParams.subscribe(params => {
      if (params['email']) {
        this.email = params['email'];
        this.otpForm.patchValue({ email: this.email });
      }
    });
  }

  verifyOtp() {
    if (this.otpForm.invalid) {
      this.notificationService.warning('Vui lòng nhập email và mã OTP hợp lệ.');
      this.otpForm.markAllAsTouched();
      return;
    }

    this.loading = true;

    this.authService.verifyOtp(this.otpForm.value as { email: string; otp_code: string }).pipe(
      catchError(err => {
        const errorMsg = err.error?.message || 'Xác thực OTP thất bại. Vui lòng thử lại.';
        this.notificationService.error(errorMsg);
        this.loading = false;
        return of(null);
      })
    ).subscribe(response => {
      this.loading = false;
      if (response) {
        this.notificationService.success('Xác thực thành công! Đang chuyển hướng đến trang đăng nhập...');
        setTimeout(() => {
          this.router.navigate(['/login']);
        }, 2000);
      }
    });
  }

  resendOtp() {
    if (!this.otpForm.value.email) {
      this.notificationService.warning('Vui lòng nhập email.');
      return;
    }

    this.loading = true;

    this.authService.resendOtp(this.otpForm.value.email).pipe(
      catchError(err => {
        const errorMsg = err.error?.message || 'Gửi lại mã OTP thất bại.';
        this.notificationService.error(errorMsg);
        this.loading = false;
        return of(null);
      })
    ).subscribe(response => {
      this.loading = false;
      if (response) {
        this.notificationService.success('Mã OTP mới đã được gửi đến email của bạn.');
      }
    });
  }

  protected readonly LOGIN_ROUTE = '/login';
  protected readonly ICON_LOCATION = ICON_LOCATION_DOT;
  protected readonly ICON_MAIL = ICON_MAIL_REGULAR;
  protected readonly ICON_PHONE = ICON_PHONE_SOLID;
}



