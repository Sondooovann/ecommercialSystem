import {Component} from '@angular/core';
import {CommonModule} from '@angular/common';
import {AuthService} from '../../../../core/services/auth.service';
import {Router, RouterLink, RouterLinkActive} from '@angular/router';
import {UserLogin} from '../../../../core/models/user.model';
import {environment} from '../../../../../environments/environment';

@Component({
  selector: 'jhi-customer-header',
  standalone: true,
  templateUrl: './customer-header.component.html',
  imports: [
    CommonModule,
    RouterLink,
    RouterLinkActive
  ],
  styleUrls: ['./customer-header.component.scss']
})
export class CustomerHeaderComponent {
  isAuthenticated = false;
  user: UserLogin | null = null;

  constructor(
    private authService: AuthService,
    private router: Router
  ) {
    this.isAuthenticated = authService.isAuthenticated();
    this.user = JSON.parse(localStorage.getItem(environment.userKey) || '{}') as UserLogin;
  }

  logout(): void {
    if (confirm('Bạn có chắc chắn muốn đăng xuất?')) {
      // Xóa tất cả dữ liệu trong localStorage
      localStorage.removeItem(environment.tokenKey);
      localStorage.removeItem(environment.userKey);
      
      // Có thể xóa thêm các items khác nếu cần
      // localStorage.clear(); // Xóa toàn bộ nếu muốn
      
      // Chuyển về trang login
      this.router.navigate(['/login']);
    }
  }
}
