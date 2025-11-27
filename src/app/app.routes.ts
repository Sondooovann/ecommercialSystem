import {Routes} from '@angular/router';
import {roleGuard} from './core/guards/role.guard';
import {authGuard} from './core/guards/auth.guard';
import {UserRole} from './core/models/user.model';
import {LoginComponent} from './pages/login/login.component';
import {CustomerLayoutComponent} from './layout/customer-layout/customer-layout.component';
import {HomeComponent} from './pages/home/home.component';
import {ProductListComponent} from './pages/product/product-list/product-list.component';
import {ProductDetailComponent} from './pages/product/product-detail/product-detail.component';
import {CartComponent} from './pages/cart/cart.component';
import {CheckoutComponent} from './pages/checkout/checkout.component';
import {OrderSuccessComponent} from './pages/order/order-success/order-success.component';
import {OrderListComponent} from './pages/order/order-list/order-list.component';
import {OrderDetailComponent} from './pages/order/order-detail/order-detail.component';
import {AboutUsComponent} from './pages/about-us/about-us.component';
import {AgencyComponent} from './pages/agency/agency.component';
import {AdminLayoutComponent} from './layout/admin-layout/admin-layout.component';

export const routes: Routes = [
  {path: '', redirectTo: 'login', pathMatch: 'full'},
  {path: 'login', component: LoginComponent},
  {
    path: 'register',
    loadComponent: () => import('./pages/register/register.component').then(m => m.RegisterComponent)
  },
  {
    path: 'verify-otp',
    loadComponent: () => import('./pages/verify-otp/verify-otp.component').then(m => m.VerifyOtpComponent)
  },

  {
    path: 'buyer',
    component: CustomerLayoutComponent,
    // canActivate: [authGuard, roleGuard],
    data: {role: UserRole.CUSTOMER},
    children: [
      {path: '', redirectTo: 'home', pathMatch: 'full'},
      {path: 'home', component: HomeComponent, data: {breadcrumb: 'Trang chủ'}},
      {path: 'product', component: ProductListComponent, data: {breadcrumb: 'Sản phẩm'}},
      {path: 'product/:id', component: ProductDetailComponent, data: {breadcrumb: 'Chi tiết sản phẩm'}},
      {path: 'cart', component: CartComponent, data: {breadcrumb: 'Giỏ hàng'}},
      {path: 'checkout', component: CheckoutComponent, data: {breadcrumb: 'Thanh toán'}},
      {path: 'order-success', component: OrderSuccessComponent, data: {breadcrumb: 'Đặt hàng thành công'}},
      {path: 'orders', component: OrderListComponent, data: {breadcrumb: 'Đơn hàng của tôi'}},
      {path: 'orders/:id', component: OrderDetailComponent, data: {breadcrumb: 'Chi tiết đơn hàng'}},
      {path: 'about-us', component: AboutUsComponent, data: {breadcrumb: 'Về chúng tôi'}},
      {path: 'agency', component: AgencyComponent, data: {breadcrumb: 'Đại lý'}}
    ]
  },

  {
    path: 'admin',
    component: AdminLayoutComponent,
    canActivate: [authGuard, roleGuard],
    data: {role: UserRole.ADMIN},
    children: [
      {path: '', redirectTo: 'dashboard', pathMatch: 'full'},
      {
        path: 'dashboard',
        loadComponent: () => import('./pages/admin/dashboard/dashboard.component').then(m => m.DashboardComponent),
        data: {breadcrumb: 'Trang chủ'}
      },
      {
        path: 'products',
        children: [
          {
            path: '',
            loadComponent: () => import('./pages/admin/products/product-list/admin-product-list.component').then(m => m.AdminProductListComponent),
            data: {breadcrumb: 'Quản lý sản phẩm'}
          },
          {
            path: 'create',
            loadComponent: () => import('./pages/admin/products/product-form/product-form.component').then(m => m.ProductFormComponent),
            data: {breadcrumb: 'Thêm sản phẩm'}
          },
          {
            path: 'edit/:id',
            loadComponent: () => import('./pages/admin/products/product-form/product-form.component').then(m => m.ProductFormComponent),
            data: {breadcrumb: 'Sửa sản phẩm'}
          }
        ]
      },
      {
        path: 'categories',
        loadComponent: () => import('./pages/admin/categories/category-list/admin-category-list.component').then(m => m.AdminCategoryListComponent),
        data: {breadcrumb: 'Quản lý danh mục'}
      },
      {
        path: 'orders',
        children: [
          {
            path: '',
            loadComponent: () => import('./pages/admin/orders/order-list/admin-order-list.component').then(m => m.AdminOrderListComponent),
            data: {breadcrumb: 'Quản lý đơn hàng'}
          },
          // {
          //   path: ':id',
          //   loadComponent: () => import('./pages/admin/orders/order-detail/admin-order-detail.component').then(m => m.AdminOrderDetailComponent),
          //   data: {breadcrumb: 'Chi tiết đơn hàng'}
          // }
        ]
      },
      {
        path: 'users',
        children: [
          {
            path: '',
            loadComponent: () => import('./pages/admin/users/user-list/admin-user-list.component').then(m => m.AdminUserListComponent),
            data: {breadcrumb: 'Quản lý người dùng'}
          },
          // {
          //   path: ':id',
          //   loadComponent: () => import('./pages/admin/users/user-detail/admin-user-detail.component').then(m => m.AdminUserDetailComponent),
          //   data: {breadcrumb: 'Chi tiết người dùng'}
          // },
          // {
          //   path: 'edit/:id',
          //   loadComponent: () => import('./pages/admin/users/user-form/admin-user-form.component').then(m => m.AdminUserFormComponent),
          //   data: {breadcrumb: 'Sửa người dùng'}
          // }
        ]
      },
      // {
      //   path: 'reports',
      //   children: [
      //     {
      //       path: '',
      //       loadComponent: () => import('./pages/admin/reports/reports.component').then(m => m.ReportsComponent),
      //       data: {breadcrumb: 'Báo cáo'}
      //     },
      //     {
      //       path: 'sales',
      //       loadComponent: () => import('./pages/admin/reports/sales-report/sales-report.component').then(m => m.SalesReportComponent),
      //       data: {breadcrumb: 'Báo cáo doanh thu'}
      //     },
      //     {
      //       path: 'inventory',
      //       loadComponent: () => import('./pages/admin/reports/inventory-report/inventory-report.component').then(m => m.InventoryReportComponent),
      //       data: {breadcrumb: 'Báo cáo tồn kho'}
      //     }
      //   ]
      // },
      // {
      //   path: 'settings',
      //   loadComponent: () => import('./pages/admin/settings/settings.component').then(m => m.SettingsComponent),
      //   data: {breadcrumb: 'Cài đặt'}
      // }
    ]
  }
];
