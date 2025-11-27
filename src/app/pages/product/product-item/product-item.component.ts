import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';

export interface ProductItem {
  id: number;
  name: string;
  price: number;
  image: string;
  description?: string;
}

@Component({
  selector: 'jhi-product-item',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './product-item.component.html',
  styleUrls: ['./product-item.component.scss']
})
export class ProductItemComponent {
  @Input() product!: ProductItem;
  @Input() type: 'grid' | 'list' = 'grid'; // mặc định là dạng lưới

  constructor(private router: Router) {}

  navigateToDetail(): void {
    this.router.navigate(['/buyer/product', this.product.id]);
  }
}
