import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, FormArray, Validators, ReactiveFormsModule } from '@angular/forms';
import { Router, ActivatedRoute } from '@angular/router';
import { ProductService } from '../../../../core/services/product.service';
import { CategoryService } from '../../../../core/services/category.service';
import { NotificationService } from '../../../../core/services/notification.service';
import { Category } from '../../../../core/models/category.model';
import { SafeHtmlPipe } from '../../../../shared/pipes/pipe-html.pipe';

interface ImagePreview {
  file: File;
  preview: string;
}

@Component({
  selector: 'jhi-product-form',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, SafeHtmlPipe],
  templateUrl: './product-form.component.html',
  styleUrls: ['./product-form.component.scss']
})
export class ProductFormComponent implements OnInit {
  productForm!: FormGroup;
  isEditMode = false;
  productId: number | null = null;
  loading = false;
  
  images: ImagePreview[] = [];
  primaryImageIndex = 0;

  // Categories từ API
  allCategories: Category[] = [];
  parentCategories: Category[] = []; // Danh mục cha (cho dropdown Loại sản phẩm)
  childCategories: Category[] = []; // Danh mục con (cho dropdown Danh mục)

  statusOptions = [
    { value: 'active', label: 'Đang bán' },
    { value: 'inactive', label: 'Ngừng bán' },
    { value: 'out_of_stock', label: 'Hết hàng' }
  ];

  attributeTypes = [
    { value: 'text', label: 'Văn bản' },
    { value: 'select', label: 'Lựa chọn' },
    { value: 'color', label: 'Màu sắc' }
  ];

  // SVG Icons
  readonly ICON_BACK = '<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" /></svg>';
  readonly ICON_ADD = '<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" /></svg>';
  readonly ICON_DELETE = '<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg>';
  readonly ICON_IMAGE = '<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg>';

  constructor(
    private fb: FormBuilder,
    private productService: ProductService,
    private categoryService: CategoryService,
    private notificationService: NotificationService,
    private router: Router,
    private route: ActivatedRoute
  ) {}

  ngOnInit(): void {
    this.initForm();
    this.loadCategories();
    
    // Check if edit mode
    this.route.paramMap.subscribe(params => {
      const id = params.get('id');
      if (id) {
        this.isEditMode = true;
        this.productId = +id;
        // TODO: Load product data
      }
    });
  }

  loadCategories(): void {
    this.loading = true;
    
    this.categoryService.getCategories().subscribe({
      next: (response) => {
        if (response.success && response.data.data) {
          this.allCategories = response.data.data;
          
          // Lọc danh mục cha (parent = null) cho dropdown "Loại sản phẩm"
          this.parentCategories = this.allCategories.filter(cat => 
            cat.parent === null && cat.status === 'active'
          );
          
          this.loading = false;
        }
      },
      error: (err) => {
        console.error('Error loading categories:', err);
        this.notificationService.error('Không thể tải danh sách danh mục');
        this.loading = false;
      }
    });
  }

  onProductTypeChange(event: Event): void {
    const selectElement = event.target as HTMLSelectElement;
    const parentId = selectElement.value;
    
    // Reset danh mục con
    this.productForm.patchValue({ category: '' });
    
    if (parentId) {
      // Lọc danh mục con theo parent đã chọn
      this.childCategories = this.allCategories.filter(cat => 
        cat.parent === parseInt(parentId) && cat.status === 'active'
      );
    } else {
      this.childCategories = [];
    }
  }

  initForm(): void {
    this.productForm = this.fb.group({
      name: ['', [Validators.required, Validators.minLength(3)]],
      product_type: ['', Validators.required], // Loại sản phẩm (danh mục cha)
      category: ['', Validators.required], // Danh mục (danh mục con)
      description: [''],
      short_description: ['', Validators.required],
      price: [0, [Validators.required, Validators.min(0)]],
      sale_price: [0, Validators.min(0)],
      stock: [0, [Validators.required, Validators.min(0)]],
      status: ['active', Validators.required],
      featured: [false],
      attributes: this.fb.array([]),
      variants: this.fb.array([])
    });
  }

  get attributes(): FormArray {
    return this.productForm.get('attributes') as FormArray;
  }

  get variants(): FormArray {
    return this.productForm.get('variants') as FormArray;
  }

  addAttribute(): void {
    const attributeGroup = this.fb.group({
      name: ['', Validators.required],
      type: ['text', Validators.required],
      values: this.fb.array([this.createAttributeValue()])
    });
    this.attributes.push(attributeGroup);
  }

  removeAttribute(index: number): void {
    this.attributes.removeAt(index);
    this.generateVariants();
  }

  getAttributeValues(attributeIndex: number): FormArray {
    return this.attributes.at(attributeIndex).get('values') as FormArray;
  }

  createAttributeValue(): FormGroup {
    return this.fb.group({
      value: ['', Validators.required],
      display: ['', Validators.required]
    });
  }

  addAttributeValue(attributeIndex: number): void {
    const values = this.getAttributeValues(attributeIndex);
    values.push(this.createAttributeValue());
  }

  removeAttributeValue(attributeIndex: number, valueIndex: number): void {
    const values = this.getAttributeValues(attributeIndex);
    values.removeAt(valueIndex);
    this.generateVariants();
  }

  generateVariants(): void {
    // Clear existing variants
    this.variants.clear();

    const attributesValue = this.attributes.value;
    if (attributesValue.length === 0) {
      // No attributes, create one default variant
      this.addVariant();
      return;
    }

    // Generate combinations
    const combinations = this.generateCombinations(attributesValue);
    combinations.forEach(combination => {
      const variantGroup = this.fb.group({
        sku: ['', Validators.required],
        price: [this.productForm.get('price')?.value || 0, [Validators.required, Validators.min(0)]],
        sale_price: [this.productForm.get('sale_price')?.value || 0, Validators.min(0)],
        stock: [this.productForm.get('stock')?.value || 0, [Validators.required, Validators.min(0)]],
        attributes: [combination]
      });
      this.variants.push(variantGroup);
    });
  }

  generateCombinations(attributes: any[]): any[] {
    if (attributes.length === 0) return [{}];
    
    const result: any[] = [];
    
    function combine(current: any, index: number) {
      if (index === attributes.length) {
        result.push({ ...current });
        return;
      }
      
      const attr = attributes[index];
      attr.values.forEach((val: any) => {
        current[attr.name] = val.value;
        combine(current, index + 1);
      });
    }
    
    combine({}, 0);
    return result;
  }

  addVariant(): void {
    const variantGroup = this.fb.group({
      sku: ['', Validators.required],
      price: [this.productForm.get('price')?.value || 0, [Validators.required, Validators.min(0)]],
      sale_price: [this.productForm.get('sale_price')?.value || 0, Validators.min(0)],
      stock: [this.productForm.get('stock')?.value || 0, [Validators.required, Validators.min(0)]],
      attributes: [{}]
    });
    this.variants.push(variantGroup);
  }

  removeVariant(index: number): void {
    this.variants.removeAt(index);
  }

  onFileSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    if (input.files && input.files.length > 0) {
      Array.from(input.files).forEach(file => {
        const reader = new FileReader();
        reader.onload = (e: any) => {
          this.images.push({
            file: file,
            preview: e.target.result
          });
        };
        reader.readAsDataURL(file);
      });
    }
  }

  removeImage(index: number): void {
    this.images.splice(index, 1);
    if (this.primaryImageIndex === index) {
      this.primaryImageIndex = 0;
    } else if (this.primaryImageIndex > index) {
      this.primaryImageIndex--;
    }
  }

  setPrimaryImage(index: number): void {
    this.primaryImageIndex = index;
  }

  onSubmit(): void {
    if (this.productForm.invalid) {
      this.notificationService.warning('Vui lòng điền đầy đủ thông tin bắt buộc');
      Object.keys(this.productForm.controls).forEach(key => {
        const control = this.productForm.get(key);
        if (control?.invalid) {
          control.markAsTouched();
        }
      });
      return;
    }

    if (this.images.length === 0) {
      this.notificationService.warning('Vui lòng tải lên ít nhất 1 hình ảnh');
      return;
    }

    this.loading = true;

    const formData = new FormData();
    const formValue = this.productForm.value;

    // Basic fields
    formData.append('name', formValue.name);
    formData.append('category', formValue.category);
    formData.append('product_type', formValue.product_type);
    formData.append('description', formValue.description);
    formData.append('short_description', formValue.short_description);
    formData.append('price', formValue.price);
    formData.append('sale_price', formValue.sale_price || '0');
    formData.append('stock', formValue.stock);
    formData.append('status', formValue.status);
    formData.append('featured', formValue.featured.toString());

    // Attributes
    formData.append('attributes', JSON.stringify(formValue.attributes));

    // Variants
    formData.append('variants', JSON.stringify(formValue.variants));

    // Images
    this.images.forEach((img, index) => {
      formData.append('images', img.file);
    });
    formData.append('primary_image_index', this.primaryImageIndex.toString());

    // Call API
    this.productService.createProduct(1, formData).subscribe({
      next: (response) => {
        if (response.success) {
          this.notificationService.success('Thêm sản phẩm thành công!');
          this.router.navigate(['/admin/products']);
        } else {
          this.notificationService.error(response.message || 'Có lỗi xảy ra');
        }
        this.loading = false;
      },
      error: (err) => {
        console.error('Error creating product:', err);
        const errorMsg = err.error?.message || 'Không thể tạo sản phẩm. Vui lòng thử lại!';
        this.notificationService.error(errorMsg);
        this.loading = false;
      }
    });
  }

  goBack(): void {
    this.router.navigate(['/admin/products']);
  }

  // Helper for template
  protected readonly Object = Object;
}

