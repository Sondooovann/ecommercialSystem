import {Component, OnInit} from '@angular/core';
import {CommonModule} from '@angular/common';
import {Router} from '@angular/router';
import {ProductService} from '../../core/services/product.service';
import {Product} from '../../core/models/product.model';
import {ProductItemComponent} from '../product/product-item/product-item.component';

interface Category {
  id: number;
  name: string;
  image: string;
  description: string;
  slug: string;
}

interface Benefit {
  icon: string;
  title: string;
  description: string;
}

@Component({
  selector: 'jhi-home',
  templateUrl: './home.component.html',
  imports: [
    CommonModule,
    ProductItemComponent
  ],
  styleUrls: ['./home.component.scss']
})
export class HomeComponent implements OnInit {
  featuredProducts: Product[] = [];
  bestSellerProducts: Product[] = [];
  loading = false;
  
  shopId = 1;

  // Categories - Các loại chè
  categories: Category[] = [
    {
      id: 1,
      name: 'Chè Shan Tuyết',
      image: 'assets/images/categories/shan-tuyet.jpg',
      description: 'Chè từ cây trà cổ thụ trên núi cao',
      slug: 'che-shan-tuyet'
    },
    {
      id: 2,
      name: 'Chè Ô Long',
      image: 'assets/images/categories/o-long.jpg',
      description: 'Chè ô long thơm ngon, hảo hạng',
      slug: 'che-o-long'
    },
    {
      id: 3,
      name: 'Chè Sen',
      image: 'assets/images/categories/sen.jpg',
      description: 'Chè ướp hương sen thanh khiết',
      slug: 'che-sen'
    },
    {
      id: 4,
      name: 'Chè Tân Cương',
      image: 'assets/images/categories/tan-cuong.jpg',
      description: 'Đặc sản chè Tân Cương Thái Nguyên',
      slug: 'che-tan-cuong'
    },
    {
      id: 5,
      name: 'Chè Hoa Nhài',
      image: 'assets/images/categories/hoa-nhai.jpg',
      description: 'Chè thơm hương hoa nhài dịu nhẹ',
      slug: 'che-hoa-nhai'
    },
    {
      id: 6,
      name: 'Chè Túi Lọc',
      image: 'assets/images/categories/tui-loc.jpg',
      description: 'Tiện lợi, dễ sử dụng',
      slug: 'che-tui-loc'
    }
  ];

  // Benefits của chè
  benefits: Benefit[] = [
    {
      icon: '🌿',
      title: '100% Tự Nhiên',
      description: 'Chè từ vùng trồng chè nổi tiếng Thái Nguyên, không chất bảo quản'
    },
    {
      icon: '✅',
      title: 'Chất Lượng Đảm Bảo',
      description: 'Kiểm tra chất lượng nghiêm ngặt, đạt chuẩn an toàn thực phẩm'
    },
    {
      icon: '🚚',
      title: 'Giao Hàng Nhanh',
      description: 'Giao hàng toàn quốc, nhanh chóng trong 2-3 ngày'
    },
    {
      icon: '💚',
      title: 'Tốt Cho Sức Khỏe',
      description: 'Giàu chất chống oxi hóa, giúp thư giãn và tốt cho sức khỏe'
    }
  ];

  constructor(
    private productService: ProductService,
    private router: Router
  ) {}

  ngOnInit(): void {
    this.loadFeaturedProducts();
    this.loadBestSellers();
  }

  loadFeaturedProducts(): void {
    this.loading = true;
    const filters = {
      status: 'active',
      sort_by: 'created_at',
      sort_order: 'desc'
    };

    this.productService.getProductsByShop(this.shopId, 1, 8, filters)
      .subscribe({
        next: (response) => {
          this.featuredProducts = response.products;
          this.loading = false;
        },
        error: (err) => {
          console.error('Error loading featured products:', err);
          this.loading = false;
        }
      });
  }

  loadBestSellers(): void {
    const filters = {
      status: 'active',
      sort_by: 'sold_count',
      sort_order: 'desc'
    };

    this.productService.getProductsByShop(this.shopId, 1, 8, filters)
      .subscribe({
        next: (response) => {
          this.bestSellerProducts = response.products;
        },
        error: (err) => {
          console.error('Error loading best sellers:', err);
        }
      });
  }

  goToCategory(slug: string): void {
    this.router.navigate(['/buyer/product'], {
      queryParams: { search: slug }
    });
  }

  goToProducts(): void {
    this.router.navigate(['/buyer/product']);
  }

  scrollToSection(sectionId: string): void {
    const element = document.getElementById(sectionId);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  }
}
