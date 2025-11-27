import { Component } from '@angular/core';
import { CustomerHeaderComponent } from '../../shared/components/header/customer/customer-header.component';
import { RouterOutlet } from '@angular/router';
import { CustomerSearchComponent } from '../../shared/components/search/customer-search.component';
import { MenuNavbarComponent } from '../../shared/components/menu-navbar/menu-navbar.component';
import { CustomerBreadcrumbComponent } from '../../shared/components/breadcumb/customer/customer-breadcrumb.component';
import { SidebarCustomerComponent } from '../../shared/components/sidebar/customer/sidebar-customer.component';

@Component({
  selector: 'app-customer-layout',
  standalone: true,
  templateUrl: './customer-layout.component.html',
  imports: [
    CustomerHeaderComponent,
    RouterOutlet,
    CustomerSearchComponent,
    MenuNavbarComponent,
    CustomerBreadcrumbComponent,
    SidebarCustomerComponent,
  ],
  styleUrls: ['./customer-layout.component.scss'],
})
export class CustomerLayoutComponent {
  sidebarBoxes = [
    {
      title: 'Danh mục chè',
      items: [
        { type: 'checkbox' as const, label: 'Chè Shan Tuyết' },
        { type: 'checkbox' as const, label: 'Chè Ô Long' },
        { type: 'checkbox' as const, label: 'Chè Sen' },
      ],
    },
    {
      title: 'Khoảng giá',
      items: [{ type: 'range' as const, label: 'Giá từ' }],
    },
    {
      title: 'Hỗ trợ khách hàng',
      items: [
        { type: 'link' as const, label: 'Hướng dẫn mua hàng', link: '/guide' },
        { type: 'link' as const, label: 'Chính sách đổi trả', link: '/policy' },
      ],
    },
  ];
}
