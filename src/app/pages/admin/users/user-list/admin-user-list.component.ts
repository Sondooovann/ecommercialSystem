import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { UserService } from '../../../../core/services/user.service';
import { User } from '../../../../core/models/user.model';
import { SafeHtmlPipe } from '../../../../shared/pipes/pipe-html.pipe';
import { ICON_SEARCH, ICON_VIEW, ICON_EDIT, ICON_TRASH } from '../../../../../assets/icons/icon';

@Component({
  selector: 'jhi-admin-user-list',
  standalone: true,
  imports: [CommonModule, FormsModule, SafeHtmlPipe],
  templateUrl: './admin-user-list.component.html',
  styleUrls: ['./admin-user-list.component.scss']
})
export class AdminUserListComponent implements OnInit {
  users: User[] = [];
  loading = false;
  error = '';

  // Filters
  searchText = '';
  selectedStatus: 'all' | 'active' | 'inactive' | 'banned' = 'all';
  selectedRole: 'all' | 'customer' | 'shop_owner' | 'admin' = 'all';

  // Pagination
  currentPage = 1;
  pageSize = 10;
  totalUsers = 0;
  totalPages = 1;

  // SVG Icons
  readonly ICON_SEARCH = ICON_SEARCH;
  readonly ICON_VIEW = ICON_VIEW;
  readonly ICON_EDIT = ICON_EDIT;
  readonly ICON_TRASH = ICON_TRASH;

  constructor(
    private userService: UserService,
    private router: Router
  ) {}

  ngOnInit(): void {
    this.loadUsers();
  }

  loadUsers(): void {
    this.loading = true;
    this.error = '';

    const filters: any = {};

    if (this.selectedStatus !== 'all') {
      filters.status = this.selectedStatus;
    }

    if (this.selectedRole !== 'all') {
      filters.role = this.selectedRole;
    }

    if (this.searchText.trim()) {
      filters.search = this.searchText.trim();
    }

    this.userService.getAdminUsers(this.currentPage, this.pageSize, filters).subscribe({
      next: (response) => {
        if (response.success && response.data?.data) {
          this.users = response.data.data.users || [];
          const pagination = response.data.data.pagination;
          this.totalUsers = pagination?.total || 0;
          this.totalPages = pagination?.pages || 1;
          this.currentPage = pagination?.current_page || 1;
        }
        this.loading = false;
      },
      error: (err) => {
        console.error('Error loading users:', err);
        this.error = 'Không thể tải danh sách người dùng';
        this.loading = false;
      }
    });
  }

  onSearch(): void {
    this.currentPage = 1;
    this.loadUsers();
  }

  onFilterChange(): void {
    this.currentPage = 1;
    this.loadUsers();
  }

  clearFilters(): void {
    this.searchText = '';
    this.selectedStatus = 'all';
    this.selectedRole = 'all';
    this.currentPage = 1;
    this.loadUsers();
  }

  onPageChange(page: number): void {
    if (page >= 1 && page <= this.totalPages) {
      this.currentPage = page;
      this.loadUsers();
    }
  }

  viewUser(userId: number): void {
    this.router.navigate(['/admin/users', userId]);
  }

  editUser(userId: number): void {
    this.router.navigate(['/admin/users/edit', userId]);
  }

  deleteUser(user: User): void {
    if (confirm(`Bạn có chắc chắn muốn xóa người dùng "${user.full_name}"?`)) {
      this.userService.deleteUser(user.id!).subscribe({
        next: (response) => {
          if (response.success) {
            alert('Xóa người dùng thành công!');
            this.loadUsers();
          }
        },
        error: (err) => {
          console.error('Error deleting user:', err);
          alert('Không thể xóa người dùng');
        }
      });
    }
  }

  toggleUserStatus(user: User): void {
    const newStatus = user.status === 'active' ? 'inactive' : 'active';
    if (confirm(`Bạn có chắc chắn muốn ${newStatus === 'active' ? 'kích hoạt' : 'vô hiệu hóa'} người dùng "${user.full_name}"?`)) {
      this.userService.updateUserStatus(user.id!, newStatus).subscribe({
        next: (response) => {
          if (response.success) {
            alert('Cập nhật trạng thái thành công!');
            this.loadUsers();
          }
        },
        error: (err) => {
          console.error('Error updating user status:', err);
          alert('Không thể cập nhật trạng thái người dùng');
        }
      });
    }
  }

  getRoleText(role: string): string {
    const roleMap: { [key: string]: string } = {
      'customer': 'Khách hàng',
      'shop_owner': 'Chủ shop',
      'admin': 'Quản trị viên'
    };
    return roleMap[role] || role;
  }

  getRoleClass(role: string): string {
    return `role-${role}`;
  }

  getStatusText(status: string): string {
    const statusMap: { [key: string]: string } = {
      'active': 'Hoạt động',
      'inactive': 'Không hoạt động',
      'banned': 'Đã khóa'
    };
    return statusMap[status] || status;
  }

  getStatusClass(status: string): string {
    return `status-${status}`;
  }

  formatDate(dateString: string): string {
    const date = new Date(dateString);
    return date.toLocaleDateString('vi-VN', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  }
}

