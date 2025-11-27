import {Component, OnInit} from '@angular/core';
import {ActivatedRoute} from '@angular/router';
import {SidebarCustomerComponent} from '../../../shared/components/sidebar/customer/sidebar-customer.component';
import {SafeHtmlPipe} from '../../../shared/pipes/pipe-html.pipe';
import {ICON_GRID_HORIZONTAL, ICON_GRID_VERTICAL} from '../../../../assets/icons/icon';
import {FormsModule} from '@angular/forms';
import {ProductService} from '../../../core/services/product.service';
import {Product} from '../../../core/models/product.model';
import {ProductItemComponent} from '../product-item/product-item.component';
import {CommonModule} from '@angular/common';

@Component({
  selector: 'jhi-product-list',
  standalone: true,
  templateUrl: './product-list.component.html',
  imports: [
    SidebarCustomerComponent,
    SafeHtmlPipe,
    FormsModule,
    ProductItemComponent,
    CommonModule
  ],
  styleUrls: ['./product-list.component.scss']
})
export class ProductListComponent implements OnInit {
  selectedSort = 'created_at'; // sort_by
  sortOrder = 'desc'; // sort_order
  sortOption = 'created_at:desc'; // Combined sort option for select dropdown
  products: Product[] = [];
  loading = false;
  error: string | null = null;
  viewMode: 'grid' | 'list' = 'grid';

  // Pagination
  currentPage = 1;
  pageSize = 10;
  totalPages = 1;
  totalProducts = 0;

  shopId = 1;

  // Filters
  searchQuery = '';
  selectedStatus = '';
  selectedCategoryId: number | undefined;

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

  protected readonly ICON_GRID_HORIZONTAL = ICON_GRID_HORIZONTAL;
  protected readonly ICON_GRID_VERTICAL = ICON_GRID_VERTICAL;

  constructor(
    private productService: ProductService,
    private route: ActivatedRoute
  ) {}

  ngOnInit(): void {
    // Lắng nghe query params từ URL
    this.route.queryParams.subscribe(params => {
      this.searchQuery = params['search'] || '';
      this.selectedStatus = params['status'] || '';
      this.selectedCategoryId = params['category_id'] ? +params['category_id'] : undefined;
      this.selectedSort = params['sort_by'] || 'created_at';
      this.sortOrder = params['sort_order'] || 'desc';
      
      // Sync sortOption với selectedSort và sortOrder
      this.sortOption = `${this.selectedSort}:${this.sortOrder}`;
      
      // Reset về trang 1 khi có filter mới
      this.currentPage = 1;
      this.loadProducts();
    });
  }

  loadProducts(): void {
    this.loading = true;
    this.error = null;

    // Nếu có category_id, sử dụng API by-category
    if (this.selectedCategoryId) {
      // Map sort options to API format
      const sortByMap: { [key: string]: string } = {
        'created_at:desc': 'latest',
        'created_at:asc': 'oldest',
        'price:asc': 'price_asc',
        'price:desc': 'price_desc',
        'name:asc': 'name_asc',
        'name:desc': 'name_desc',
        'sold_count:desc': 'best_selling'
      };

      const sortBy = sortByMap[`${this.selectedSort}:${this.sortOrder}`] || 'latest';

      this.productService.getProductsByCategory(
        this.selectedCategoryId,
        this.currentPage,
        this.pageSize,
        sortBy
      ).subscribe({
        next: (response) => {
          this.products = response.products;
          this.currentPage = response.pagination.page;
          this.pageSize = response.pagination.page_size;
          this.totalPages = response.pagination.total_pages;
          this.totalProducts = response.pagination.total;
          this.loading = false;
        },
        error: (err) => {
          this.error = err.message || 'Có lỗi xảy ra khi tải sản phẩm';
          this.loading = false;
          console.error('Error loading products:', err);
        }
      });
    } else {
      // Nếu không có category_id, sử dụng API by-shop (tất cả sản phẩm)
      const filters = {
        search: this.searchQuery || undefined,
        status: this.selectedStatus || undefined,
        sort_by: this.selectedSort,
        sort_order: this.sortOrder
      };

      this.productService.getProductsByShop(this.shopId, this.currentPage, this.pageSize, filters)
        .subscribe({
          next: (response) => {
            this.products = response.products;
            this.currentPage = response.pagination.page;
            this.pageSize = response.pagination.page_size;
            this.totalPages = response.pagination.total_pages;
            this.totalProducts = response.pagination.total;
            this.loading = false;
          },
          error: (err) => {
            this.error = err.message || 'Có lỗi xảy ra khi tải sản phẩm';
            this.loading = false;
            console.error('Error loading products:', err);
          }
        });
    }
  }

  onSortOptionChange(): void {
    // Parse sortOption thành sort_by và sort_order
    const [sortBy, sortOrder] = this.sortOption.split(':');
    this.selectedSort = sortBy;
    this.sortOrder = sortOrder;
    
    this.currentPage = 1;
    this.loadProducts();
  }

  onPageChange(page: number): void {
    if (page >= 1 && page <= this.totalPages) {
      this.currentPage = page;
      this.loadProducts();
    }
  }

  setViewMode(mode: 'grid' | 'list'): void {
    this.viewMode = mode;
  }
}
