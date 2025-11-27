import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { ProductService, TopSellingProduct } from '../../../core/services/product.service';

@Component({
  selector: 'jhi-top-selling',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './top-selling.component.html',
  styleUrls: ['./top-selling.component.scss']
})
export class TopSellingComponent implements OnInit {
  products: TopSellingProduct[] = [];
  loading = false;
  error: string | null = null;

  constructor(
    private productService: ProductService,
    private router: Router
  ) {}

  ngOnInit(): void {
    this.loadTopSelling();
  }

  loadTopSelling(): void {
    this.loading = true;
    this.error = null;

    this.productService.getTopSellingProducts().subscribe({
      next: (data) => {
        this.products = data;
        this.loading = false;
      },
      error: (err) => {
        this.error = 'Không thể tải sản phẩm bán chạy';
        this.loading = false;
        console.error(err);
      }
    });
  }

  navigateToProduct(productId: number): void {
    this.router.navigate(['/buyer/product', productId]);
  }
}

