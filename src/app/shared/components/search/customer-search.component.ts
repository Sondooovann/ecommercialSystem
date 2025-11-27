import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { SafeHtmlPipe } from '../../pipes/pipe-html.pipe';
import {ICON_CART, ICON_CART_WHITE, ICON_SEARCH} from '../../../../assets/icons/icon';
import { FormsModule } from '@angular/forms';
import { NgForOf } from '@angular/common';
import { CartModalComponent } from '../cart-modal/cart-modal.component';

@Component({
  selector: 'jhi-customer-search',
  standalone: true,
  templateUrl: './customer-search.component.html',
  imports: [
    SafeHtmlPipe,
    FormsModule,
    NgForOf,
    CommonModule,
    CartModalComponent
  ],
  styleUrls: ['./customer-search.component.scss']
})
export class CustomerSearchComponent {
  searchText = '';
  showCartModal = false;
  quickKeywords = [
    'Trà Thái Nguyên',
    'Trà Ô Long',
    'Trà Sen',
    'Trà Nhài',
    'Trà Túi Lọc',
    'Trà Shan Tuyết',
    'Trà Đen',
    'Hộp Trà Quà Tặng',
    'Trà Tấm',
    'Trà Đông Trùng Hạ Thảo'
  ];

  constructor(private router: Router) {}

  onSearch() {
    if (this.searchText.trim()) {
      // Navigate đến trang product list với query params search
      this.router.navigate(['/buyer/product'], {
        queryParams: {
          search: this.searchText.trim()
        }
      });
    }
  }

  searchQuick(keyword: string) {
    // Tìm kiếm nhanh bằng keyword (tên sản phẩm hoặc category)
    this.router.navigate(['/buyer/product'], {
      queryParams: {
        search: keyword
      }
    });
  }

  goToCart(){
    this.showCartModal = true;
  }

  closeCartModal(): void {
    this.showCartModal = false;
  }

  protected readonly ICON_SEARCH = ICON_SEARCH;
  protected readonly ICON_CART = ICON_CART_WHITE;
}
