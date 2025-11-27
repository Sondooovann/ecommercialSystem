import {Component, ViewEncapsulation} from '@angular/core';
import {FormControl, FormGroup, NgSelectOption, ReactiveFormsModule, Validators} from '@angular/forms';
import {
  ICON_EYE_LINEAR,
  ICON_EYE_SLASH_LINEAR,
  ICON_LOCATION_DOT,
  ICON_LOCK_LINEAR, ICON_MAIL_REGULAR, ICON_PHONE_SOLID,
  ICON_USER_LINEAR
} from '../../../assets/icons/icon';
import {SafeHtmlPipe} from '../../shared/pipes/pipe-html.pipe';
import {Router} from '@angular/router';
import {AuthService} from '../../core/services/auth.service';
import {NotificationService} from '../../core/services/notification.service';
import {catchError, of} from 'rxjs';
import {LoginRequest} from '../../core/models/user.model';

@Component({
  selector: 'jhi-login',
  standalone: true,
  templateUrl: './login.component.html',
  imports: [
    ReactiveFormsModule,
    SafeHtmlPipe
  ],
  styleUrls: ['./login.component.scss', './../../../styles/scss/global.scss'],
})
export class LoginComponent {
  passwordVisible: boolean = false;
  loading = false;

  loginForm = new FormGroup({
    email: new FormControl('', [Validators.required, Validators.email]),
    password: new FormControl('', Validators.required)
  });

  constructor(
    private authService: AuthService,
    private router: Router,
    private notificationService: NotificationService
  ) {}

  showPassword(event: Event) {
    event.preventDefault();
    event.stopPropagation();
    this.passwordVisible = !this.passwordVisible;
  }

  login(){
    if (this.loginForm.invalid) {
      this.notificationService.warning('Vui lòng nhập đầy đủ thông tin đăng nhập.');
      this.loginForm.markAllAsTouched();
      return;
    }

    this.loading = true;

    this.authService.login(this.loginForm.value as LoginRequest).pipe(
      catchError(err => {
        const errorMsg = err.error?.message || 'Đăng nhập thất bại. Vui lòng thử lại.';
        this.notificationService.error(errorMsg);
        this.loading = false;
        return of(null);
      })
    ).subscribe(response => {
      this.loading = false;
      if (response) {
        this.notificationService.success('Đăng nhập thành công!');
        const role = response.user?.role;
        if (role === 'ADMIN' || role === 'admin') {
          this.router.navigate(['/admin']);
        } else {
          this.router.navigate(['/buyer']);
        }
      }
    });

  }

  protected readonly REGISTER_ROUTE = '/register';
  protected readonly ICON_USER = ICON_USER_LINEAR;
  protected readonly ICON_LOCK = ICON_LOCK_LINEAR;
  protected readonly ICON_EYE = ICON_EYE_LINEAR;
  protected readonly ICON_EYE_SLASH = ICON_EYE_SLASH_LINEAR;
  protected readonly ICON_LOCATION = ICON_LOCATION_DOT;
  protected readonly ICON_MAIL = ICON_MAIL_REGULAR;
  protected readonly ICON_PHONE = ICON_PHONE_SOLID;
}
