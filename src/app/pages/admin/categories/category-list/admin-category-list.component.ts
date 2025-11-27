import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { CategoryService } from '../../../../core/services/category.service';
import { NotificationService } from '../../../../core/services/notification.service';
import { Category, CategoryTreeNode } from '../../../../core/models/category.model';
import { SafeHtmlPipe } from '../../../../shared/pipes/pipe-html.pipe';
import { ICON_EDIT, ICON_SEARCH, ICON_TRASH, ICON_PLUS } from '../../../../../assets/icons/icon';

@Component({
  selector: 'jhi-admin-category-list',
  standalone: true,
  imports: [CommonModule, FormsModule, SafeHtmlPipe],
  templateUrl: './admin-category-list.component.html',
  styleUrls: ['./admin-category-list.component.scss']
})
export class AdminCategoryListComponent implements OnInit {
  categories: Category[] = [];
  filteredCategories: Category[] = [];
  categoryTree: CategoryTreeNode[] = [];
  loading = false;
  error = '';
  
  // Modal
  showModal = false;
  modalMode: 'create' | 'edit' = 'create';
  selectedCategory: Category | null = null;
  
  // Form data
  formData = {
    name: '',
    description: '',
    is_active: true,
    parent: '',
    image: null as File | null
  };
  
  // Filters
  searchText = '';
  selectedStatus: 'all' | 'active' | 'inactive' = 'all';
  showAsTree = true; // Mặc định hiển thị dạng cây
  
  // Expanded state for tree nodes
  expandedNodes: Set<number> = new Set();
  
  // Icons
  readonly ICON_SEARCH = ICON_SEARCH;
  readonly ICON_ADD = ICON_PLUS;
  readonly ICON_EDIT = ICON_EDIT;
  readonly ICON_DELETE = ICON_TRASH;
  
  constructor(
    private categoryService: CategoryService,
    private notificationService: NotificationService
  ) {}
  
  ngOnInit(): void {
    this.loadCategories();
    // Mở rộng tất cả nodes cha mặc định
    this.expandAllParentNodes();
  }
  
  loadCategories(): void {
    this.loading = true;
    this.error = '';
    
    this.categoryService.getCategories().subscribe({
      next: (response) => {
        if (response.success && response.data.data) {
          this.categories = response.data.data;
          this.applyFilters();
          this.buildTree();
        }
        this.loading = false;
      },
      error: (err) => {
        console.error('Error loading categories:', err);
        this.error = 'Không thể tải danh sách danh mục';
        this.notificationService.error('Không thể tải danh sách danh mục');
        this.loading = false;
      }
    });
  }
  
  applyFilters(): void {
    let filtered = [...this.categories];
    
    // Filter by search text
    if (this.searchText.trim()) {
      const search = this.searchText.toLowerCase();
      filtered = filtered.filter(cat => 
        cat.name.toLowerCase().includes(search)
      );
    }
    
    // Filter by status
    if (this.selectedStatus !== 'all') {
      filtered = filtered.filter(cat => cat.status === this.selectedStatus);
    }
    
    this.filteredCategories = filtered;
  }
  
  buildTree(): void {
    this.categoryTree = this.categoryService.buildCategoryTree(this.filteredCategories);
  }
  
  onSearch(): void {
    this.applyFilters();
    this.buildTree();
  }
  
  onFilterChange(): void {
    this.applyFilters();
    this.buildTree();
  }
  
  toggleViewMode(): void {
    this.showAsTree = !this.showAsTree;
  }
  
  openCreateModal(): void {
    this.modalMode = 'create';
    this.selectedCategory = null;
    this.resetForm();
    this.showModal = true;
  }
  
  openEditModal(category: Category): void {
    this.modalMode = 'edit';
    this.selectedCategory = category;
    this.formData = {
      name: category.name,
      description: category.description || '',
      is_active: category.status === 'active',
      parent: category.parent ? category.parent.toString() : '',
      image: null
    };
    this.showModal = true;
  }
  
  closeModal(): void {
    this.showModal = false;
    this.resetForm();
  }
  
  resetForm(): void {
    this.formData = {
      name: '',
      description: '',
      is_active: true,
      parent: '',
      image: null
    };
  }
  
  onImageSelected(event: any): void {
    const file = event.target.files[0];
    if (file) {
      this.formData.image = file;
    }
  }
  
  submitForm(): void {
    if (!this.formData.name.trim()) {
      this.notificationService.warning('Vui lòng nhập tên danh mục');
      return;
    }
    
    if (this.modalMode === 'create') {
      this.createCategory();
    } else {
      this.updateCategory();
    }
  }
  
  createCategory(): void {
    this.loading = true;
    
    this.categoryService.createCategory(this.formData).subscribe({
      next: (response) => {
        console.log('Category created:', response);
        this.notificationService.success('Tạo danh mục thành công!');
        this.closeModal();
        this.loadCategories();
      },
      error: (err) => {
        console.error('Error creating category:', err);
        this.notificationService.error('Không thể tạo danh mục. Vui lòng thử lại!');
        this.loading = false;
      }
    });
  }
  
  updateCategory(): void {
    if (!this.selectedCategory) return;
    
    this.loading = true;
    
    this.categoryService.updateCategory(this.selectedCategory.id, this.formData).subscribe({
      next: (response) => {
        console.log('Category updated:', response);
        this.notificationService.success('Cập nhật danh mục thành công!');
        this.closeModal();
        this.loadCategories();
      },
      error: (err) => {
        console.error('Error updating category:', err);
        this.notificationService.error('Không thể cập nhật danh mục. Vui lòng thử lại!');
        this.loading = false;
      }
    });
  }
  
  deleteCategory(category: Category): void {
    // Check if category has children
    const hasChildren = this.categories.some(cat => cat.parent === category.id);
    
    if (hasChildren) {
      this.notificationService.warning('Không thể xóa danh mục này vì còn danh mục con. Vui lòng xóa các danh mục con trước.');
      return;
    }
    
    if (confirm(`Bạn có chắc chắn muốn xóa danh mục "${category.name}"?`)) {
      this.loading = true;
      
      this.categoryService.deleteCategory(category.id).subscribe({
        next: (response) => {
          console.log('Category deleted:', response);
          this.notificationService.success('Xóa danh mục thành công!');
          this.loadCategories();
        },
        error: (err) => {
          console.error('Error deleting category:', err);
          this.notificationService.error('Không thể xóa danh mục. Vui lòng thử lại!');
          this.loading = false;
        }
      });
    }
  }
  
  getParentCategories(): Category[] {
    return this.categories.filter(cat => cat.parent === null);
  }
  
  getCategoryName(categoryId: number | null): string {
    if (!categoryId) return 'Không có';
    const category = this.categories.find(cat => cat.id === categoryId);
    return category ? category.name : 'N/A';
  }
  
  getStatusText(status: string): string {
    return status === 'active' ? 'Hoạt động' : 'Không hoạt động';
  }
  
  getStatusClass(status: string): string {
    return `status-${status}`;
  }
  
  getChildrenCount(categoryId: number): number {
    return this.categories.filter(cat => cat.parent === categoryId).length;
  }
  
  renderCategoryTree(nodes: CategoryTreeNode[], level: number = 0): CategoryTreeNode[] {
    const result: CategoryTreeNode[] = [];
    
    nodes.forEach(node => {
      result.push({ ...node, level });
      if (node.children && node.children.length > 0) {
        result.push(...this.renderCategoryTree(node.children, level + 1));
      }
    });
    
    return result;
  }
  
  getFlattenedTree(): CategoryTreeNode[] {
    return this.renderCategoryTree(this.categoryTree);
  }
  
  // Expand/Collapse functionality
  toggleNode(categoryId: number): void {
    if (this.expandedNodes.has(categoryId)) {
      this.expandedNodes.delete(categoryId);
    } else {
      this.expandedNodes.add(categoryId);
    }
  }
  
  isExpanded(categoryId: number): boolean {
    return this.expandedNodes.has(categoryId);
  }
  
  hasChildren(categoryId: number): boolean {
    return this.getChildrenCount(categoryId) > 0;
  }
  
  expandAllParentNodes(): void {
    // Mở rộng tất cả các categories có con
    this.categories.forEach(cat => {
      if (this.getChildrenCount(cat.id) > 0) {
        this.expandedNodes.add(cat.id);
      }
    });
  }
  
  collapseAllNodes(): void {
    this.expandedNodes.clear();
  }
  
  // Render tree với expand/collapse
  getTreeWithExpandState(): CategoryTreeNode[] {
    return this.renderTreeWithExpand(this.categoryTree);
  }
  
  private renderTreeWithExpand(nodes: CategoryTreeNode[], level: number = 0): CategoryTreeNode[] {
    const result: CategoryTreeNode[] = [];
    
    nodes.forEach(node => {
      result.push({ ...node, level });
      
      // Chỉ hiển thị children nếu node được expand
      if (node.children && node.children.length > 0 && this.isExpanded(node.id)) {
        result.push(...this.renderTreeWithExpand(node.children, level + 1));
      }
    });
    
    return result;
  }
}

