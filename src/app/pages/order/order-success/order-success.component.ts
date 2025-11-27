import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, ActivatedRoute } from '@angular/router';
import { SafeHtmlPipe } from '../../../shared/pipes/pipe-html.pipe';

@Component({
  selector: 'jhi-order-success',
  standalone: true,
  imports: [CommonModule, SafeHtmlPipe],
  templateUrl: './order-success.component.html',
  styleUrls: ['./order-success.component.scss']
})
export class OrderSuccessComponent implements OnInit {
  orderId: string = '';
  orderAmount: string = '';

  constructor(
    private router: Router,
    private route: ActivatedRoute
  ) {}

  ngOnInit(): void {
    // Lấy orderId và amount từ query params
    this.route.queryParams.subscribe(params => {
      this.orderId = params['orderId'] || '';
      this.orderAmount = params['amount'] || '0';
    });
  }

  goToHome(): void {
    this.router.navigate(['/buyer/home']);
  }

  goToOrderList(): void {
    this.router.navigate(['/buyer/orders']);
  }

  formatPrice(price: string | number): string {
    const numPrice = typeof price === 'string' ? parseFloat(price) : price;
    return numPrice.toLocaleString('vi-VN') + '₫';
  }
}

