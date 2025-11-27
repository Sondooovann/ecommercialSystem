import {Component, OnInit} from '@angular/core';
import {CommonModule} from '@angular/common';
import {Router} from '@angular/router';
import {FormsModule} from '@angular/forms';
import {ProductService} from '../../../../core/services/product.service';
import {Product} from '../../../../core/models/product.model';
import {SafeHtmlPipe} from '../../../../shared/pipes/pipe-html.pipe';
import {ICON_EDIT, ICON_SEARCH, ICON_TRASH, ICON_VIEW} from '../../../../../assets/icons/icon';

@Component({
  selector: 'jhi-admin-product-list',
  standalone: true,
  imports: [CommonModule, FormsModule, SafeHtmlPipe],
  templateUrl: './admin-product-list.component.html',
  styleUrls: ['./admin-product-list.component.scss']
})
export class AdminProductListComponent implements OnInit {
  products: Product[] = [];
  filteredProducts: Product[] = [];
  loading = false;
  error = '';

  // Filters
  searchText = '';
  selectedStatus: 'all' | 'active' | 'inactive' | 'out_of_stock' = 'all';
  selectedCategory = 'all';

  // Pagination
  currentPage = 1;
  pageSize = 10;
  totalProducts = 0;
  totalPages = 1;

  // SVG Icons
  readonly ICON_SEARCH = ICON_SEARCH;
  readonly ICON_ADD = '<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" /></svg>';
  readonly ICON_EDIT = ICON_EDIT;
  readonly ICON_DELETE = ICON_TRASH;
  readonly ICON_VIEW = ICON_VIEW;
  constructor(
    private productService: ProductService,
    private router: Router
  ) {
  }

  ngOnInit(): void {
    this.loadProducts();
  }

  loadProducts(): void {
    this.loading = true;
    this.error = '';

    const filters = {
      status: this.selectedStatus === 'all' ? undefined : this.selectedStatus,
      search: this.searchText || undefined,
      sort_by: 'created_at',
      sort_order: 'desc'
    };

    this.productService.getProductsByShop(1, this.currentPage, this.pageSize, filters).subscribe({
      next: (response) => {
        this.products = response.products;
        this.filteredProducts = this.products;
        this.totalProducts = response.pagination?.total || this.products.length;
        this.totalPages = response.pagination?.total_pages || 1;
        this.loading = false;
      },
      error: (err) => {
        console.error('Error loading products:', err);
        this.error = 'Không thể tải danh sách sản phẩm';
        this.loading = false;
      }
    });
  }

  onSearch(): void {
    this.currentPage = 1;
    this.loadProducts();
  }

  onFilterChange(): void {
    this.currentPage = 1;
    this.loadProducts();
  }

  onPageChange(page: number): void {
    if (page >= 1 && page <= this.totalPages) {
      this.currentPage = page;
      this.loadProducts();
    }
  }

  createProduct(): void {
    this.router.navigate(['/admin/products/create']);
  }

  editProduct(productId: number): void {
    this.router.navigate(['/admin/products/edit', productId]);
  }

  viewProduct(productId: number): void {
    this.router.navigate(['/buyer/product', productId]);
  }

  deleteProduct(product: Product): void {
    if (confirm(`Bạn có chắc chắn muốn xóa sản phẩm "${product.name}"?`)) {
      // TODO: Call API to delete product
      alert('Chức năng xóa sản phẩm đang được phát triển');
    }
  }

  formatPrice(price: string | number): string {
    const numPrice = typeof price === 'string' ? parseFloat(price) : price;
    return numPrice.toLocaleString('vi-VN') + '₫';
  }

  getStatusText(status: string): string {
    const statusMap: { [key: string]: string } = {
      'active': 'Đang bán',
      'inactive': 'Ngừng bán',
      'out_of_stock': 'Hết hàng'
    };
    return statusMap[status] || status;
  }

  getStatusClass(status: string): string {
    return `status-${status}`;
  }

  getPlaceholderImage(): string {
    return 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCIgZmlsbD0iI2YwZjBmMCIvPjx0ZXh0IHg9IjUwJSIgeT0iNTAlIiBmb250LWZhbWlseT0iQXJpYWwiIGZvbnQtc2l6ZT0iMTQiIGZpbGw9IiM5OTkiIHRleHQtYW5jaG9yPSJtaWRkbGUiIGR5PSIuM2VtIj5ObyBJbWFnZTwvdGV4dD48L3N2Zz4=';
  }

  onImageError(event: Event): void {
    const img = event.target as HTMLImageElement;
    img.src = this.getPlaceholderImage();
  }

  protected readonly parseFloat = parseFloat;
}

