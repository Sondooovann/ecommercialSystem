import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { Category, CategoryResponse, CategoryCreateRequest, CategoryUpdateRequest } from '../models/category.model';

@Injectable({
  providedIn: 'root'
})
export class CategoryService {
  private apiUrl = 'http://localhost:8000/api/products/categories';

  constructor(private http: HttpClient) {}

  // Get all categories
  getCategories(): Observable<CategoryResponse> {
    return this.http.get<CategoryResponse>(`${this.apiUrl}/`);
  }

  // Get category by id
  getCategoryById(id: number): Observable<any> {
    return this.http.get<any>(`${this.apiUrl}/${id}/`);
  }

  // Create category
  createCategory(data: CategoryCreateRequest): Observable<any> {
    const formData = new FormData();
    formData.append('name', data.name);
    formData.append('is_active', data.is_active.toString());
    
    if (data.description) {
      formData.append('description', data.description);
    }
    
    if (data.parent) {
      formData.append('parent', data.parent.toString());
    }
    
    if (data.image) {
      formData.append('image', data.image);
    }

    return this.http.post<any>(`${this.apiUrl}/create/`, formData);
  }

  // Update category
  updateCategory(id: number, data: CategoryUpdateRequest): Observable<any> {
    const formData = new FormData();
    
    if (data.name) {
      formData.append('name', data.name);
    }
    
    if (data.description !== undefined) {
      formData.append('description', data.description);
    }
    
    if (data.is_active !== undefined) {
      formData.append('is_active', data.is_active.toString());
    }
    
    if (data.parent !== undefined) {
      formData.append('parent', data.parent ? data.parent.toString() : '');
    }
    
    if (data.image) {
      formData.append('image', data.image);
    }

    return this.http.put<any>(`${this.apiUrl}/${id}/update/`, formData);
  }

  // Delete category
  deleteCategory(id: number): Observable<any> {
    return this.http.delete<any>(`${this.apiUrl}/${id}/delete/`);
  }

  // Build category tree
  buildCategoryTree(categories: Category[]): any[] {
    const categoryMap = new Map<number, any>();
    const rootCategories: any[] = [];

    // Create map of all categories
    categories.forEach(category => {
      categoryMap.set(category.id, { ...category, children: [] });
    });

    // Build tree structure
    categories.forEach(category => {
      const node = categoryMap.get(category.id);
      if (category.parent === null) {
        rootCategories.push(node);
      } else {
        const parent = categoryMap.get(category.parent);
        if (parent) {
          parent.children.push(node);
        }
      }
    });

    return rootCategories;
  }

  // Get parent categories (categories without parent)
  getParentCategories(categories: Category[]): Category[] {
    return categories.filter(cat => cat.parent === null);
  }

  // Get child categories of a parent
  getChildCategories(categories: Category[], parentId: number): Category[] {
    return categories.filter(cat => cat.parent === parentId);
  }
}

