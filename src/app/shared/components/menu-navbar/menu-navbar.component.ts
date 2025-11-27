import {Component, OnInit} from '@angular/core';
import {RouterLink} from '@angular/router';
import {CommonModule} from '@angular/common';
import {CategoryService} from '../../../core/services/category.service';
import {Category} from '../../../core/models/category.model';

@Component({
  selector: 'jhi-menu-navbar',
  standalone: true,
  templateUrl: './menu-navbar.component.html',
  imports: [
    RouterLink,
    CommonModule
  ],
  styleUrls: ['./menu-navbar.component.scss']
})
export class MenuNavbarComponent implements OnInit {
  categories: Category[] = [];
  loading = false;

  constructor(private categoryService: CategoryService) {}

  ngOnInit(): void {
    this.loadCategories();
  }

  loadCategories(): void {
    this.loading = true;
    this.categoryService.getCategories().subscribe({
      next: (response) => {
        if (response.success && response.data.data) {
          // Lọc chỉ lấy categories có status = 'active' và parent = null (categories chính)
          this.categories = response.data.data.filter(cat => 
            cat.status === 'active' && cat.parent === null
          );
        }
        this.loading = false;
      },
      error: (err) => {
        console.error('Error loading categories:', err);
        this.loading = false;
      }
    });
  }
}
