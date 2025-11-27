import {Component, OnInit} from '@angular/core';
import {ProductDetail, ProductVariant} from '../../../core/models/product.model';
import {ActivatedRoute, Router} from '@angular/router';
import {ProductService} from '../../../core/services/product.service';
import {BreadcrumbService} from '../../../core/services/breadcrumb.service';
import {CartService} from '../../../core/services/cart.service';
import {CommonModule} from '@angular/common';
import {FormsModule} from '@angular/forms';
import {ICON_CART, ICON_CART_WHITE} from '../../../../assets/icons/icon';
import {SafeHtmlPipe} from '../../../shared/pipes/pipe-html.pipe';
import {TopSellingComponent} from '../../../shared/components/top-selling/top-selling.component';

@Component({
  selector: 'jhi-product-detail',
  standalone: true,
  imports: [CommonModule, FormsModule, SafeHtmlPipe, TopSellingComponent],
  templateUrl: './product-detail.component.html',
  styleUrls: ['./product-detail.component.scss']
})
export class ProductDetailComponent implements OnInit {
  productId!: number;
  product?: ProductDetail;
  loading = false;
  error: string | null = null;

  // Image handling
  selectedImage: string = '';

  // Quantity
  quantity: number = 1;

  // Selected variant
  selectedVariant: ProductVariant | null = null;

  // Selected variant attributes
  selectedAttributes: { [key: string]: string } = {};

  // Cart notifications
  cartMessage: string = '';
  showCartMessage: boolean = false;

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private productService: ProductService,
    private breadcrumbService: BreadcrumbService,
    private cartService: CartService
  ) {}

  ngOnInit(): void {
    this.route.paramMap.subscribe(params => {
      const idParam = params.get('id');
      if (idParam) {
        this.productId = +idParam;
        this.loadProductDetail();
      }
    });
  }

  loadProductDetail(): void {
    this.loading = true;
    this.error = null;

    this.productService.getProductDetail(this.productId)
      .subscribe({
        next: (data) => {
          this.product = data;

          // Update breadcrumb with product name
          // @ts-ignore
          this.breadcrumbService.updateLastBreadcrumb(this.product.name);

          // Set first image as selected
          if (this.product?.images && this.product.images.length > 0) {
            const thumbnail = this.product.images.find(img => img.is_thumbnail);
            this.selectedImage = thumbnail ? thumbnail.image_url : this.product.images[0].image_url;
          }
          this.loading = false;
        },
        error: (err) => {
          this.error = 'Không thể tải chi tiết sản phẩm';
          this.loading = false;
          console.error(err);
        },
      });
  }

  selectImage(imageUrl: string): void {
    this.selectedImage = imageUrl;
  }

  increaseQuantity(): void {
    const maxStock = this.getCurrentStock();
    if (this.quantity < maxStock) {
      this.quantity++;
    }
  }

  decreaseQuantity(): void {
    if (this.quantity > 1) {
      this.quantity--;
    }
  }

  addToCart(): void {
    if (!this.product) {
      this.showMessage('Không tìm thấy sản phẩm!', 'error');
      return;
    }

    // Kiểm tra xem sản phẩm có variants không
    if (this.product.variants && this.product.variants.length > 0) {
      if (!this.selectedVariant) {
        this.showMessage('Vui lòng chọn phân loại hàng!', 'error');
        return;
      }

      // Kiểm tra số lượng trong kho của variant
      if (this.quantity > this.selectedVariant.stock) {
        this.showMessage('Số lượng vượt quá số lượng có sẵn!', 'error');
        return;
      }
    } else {
      // Kiểm tra số lượng trong kho của sản phẩm
      if (this.quantity > this.product.stock) {
        this.showMessage('Số lượng vượt quá số lượng có sẵn!', 'error');
        return;
      }
    }

    const cartData = {
      variant_id: this.selectedVariant ? this.selectedVariant.id : null,
      quantity: this.quantity
    };

    this.cartService.addToCartWithVariant(cartData.variant_id, cartData.quantity)
      .subscribe({
        next: (response) => {
          console.log('Thêm vào giỏ hàng thành công:', response);
          this.showMessage('Đã thêm sản phẩm vào giỏ hàng!', 'success');
          // Reset quantity sau khi thêm thành công
          this.quantity = 1;
        },
        error: (error) => {
          console.error('Lỗi khi thêm vào giỏ hàng:', error);
          const errorMessage = error.error?.message || 'Không thể thêm vào giỏ hàng. Vui lòng thử lại!';
          this.showMessage(errorMessage, 'error');
        }
      });
  }

  showMessage(message: string, type: 'success' | 'error'): void {
    this.cartMessage = message;
    this.showCartMessage = true;
    
    // Tự động ẩn thông báo sau 3 giây
    setTimeout(() => {
      this.showCartMessage = false;
      this.cartMessage = '';
    }, 3000);
  }

  selectVariant(variant: ProductVariant): void {
    this.selectedVariant = variant;
    // Cập nhật giá khi chọn variant
    if (variant.image_url) {
      this.selectedImage = variant.image_url;
    }
  }

  buyNow(): void {
    if (!this.product) {
      this.showMessage('Không tìm thấy sản phẩm!', 'error');
      return;
    }

    // Kiểm tra xem sản phẩm có variants không
    if (this.product.variants && this.product.variants.length > 0) {
      if (!this.selectedVariant) {
        this.showMessage('Vui lòng chọn phân loại hàng!', 'error');
        return;
      }

      // Kiểm tra số lượng trong kho của variant
      if (this.quantity > this.selectedVariant.stock) {
        this.showMessage('Số lượng vượt quá số lượng có sẵn!', 'error');
        return;
      }
    } else {
      // Kiểm tra số lượng trong kho của sản phẩm
      if (this.quantity > this.product.stock) {
        this.showMessage('Số lượng vượt quá số lượng có sẵn!', 'error');
        return;
      }
    }

    const cartData = {
      variant_id: this.selectedVariant ? this.selectedVariant.id : null,
      quantity: this.quantity
    };

    // Thêm vào giỏ hàng và chuyển ngay đến trang thanh toán
    this.cartService.addToCartWithVariant(cartData.variant_id, cartData.quantity)
      .subscribe({
        next: (response) => {
          console.log('Thêm vào giỏ hàng và chuyển đến thanh toán:', response);
          // Chuyển ngay đến trang checkout
          this.router.navigate(['/buyer/checkout']);
        },
        error: (error) => {
          console.error('Lỗi khi thêm vào giỏ hàng:', error);
          const errorMessage = error.error?.message || 'Không thể thêm vào giỏ hàng. Vui lòng thử lại!';
          this.showMessage(errorMessage, 'error');
        }
      });
  }

  goBack(): void {
    this.router.navigate(['/buyer/product']);
  }

  getDiscountPercent(): number {
    if (!this.product) return 0;
    const price = parseFloat(this.getCurrentPrice());
    const salePrice = parseFloat(this.getCurrentSalePrice());
    if (price > 0 && salePrice < price) {
      return Math.round(((price - salePrice) / price) * 100);
    }
    return 0;
  }

  getCurrentPrice(): string {
    if (this.selectedVariant) {
      return this.selectedVariant.price;
    }
    return this.product?.price || '0';
  }

  getCurrentSalePrice(): string {
    if (this.selectedVariant) {
      return this.selectedVariant.sale_price;
    }
    return this.product?.sale_price || '0';
  }

  getCurrentStock(): number {
    if (this.selectedVariant) {
      return this.selectedVariant.stock;
    }
    return this.product?.stock || 0;
  }

  protected readonly ICON_CART_WHITE = ICON_CART_WHITE;
  protected readonly ICON_CART = ICON_CART;
}
