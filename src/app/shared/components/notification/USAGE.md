# Hướng dẫn sử dụng Notification Service

## Mô tả
Service thông báo hiển thị các message ở góc trên bên phải màn hình với 4 loại thông báo:
- ✅ **Success** (Thành công) - màu xanh lá
- ❌ **Error** (Lỗi) - màu đỏ  
- ⚠️ **Warning** (Cảnh báo) - màu vàng
- ℹ️ **Info** (Thông tin) - màu xanh dương

## Cách sử dụng

### 1. Import NotificationService vào Component

```typescript
import { NotificationService } from '../../../core/services/notification.service';

export class YourComponent {
  constructor(private notificationService: NotificationService) {}
}
```

### 2. Hiển thị thông báo

#### Thông báo thành công
```typescript
this.notificationService.success('Đã lưu thành công!');
// hoặc với thời gian tùy chỉnh (ms)
this.notificationService.success('Đã lưu thành công!', 5000);
```

#### Thông báo lỗi
```typescript
this.notificationService.error('Có lỗi xảy ra, vui lòng thử lại!');
```

#### Thông báo cảnh báo
```typescript
this.notificationService.warning('Dữ liệu sắp hết hạn!');
```

#### Thông báo thông tin
```typescript
this.notificationService.info('Đang xử lý yêu cầu của bạn...');
```

## Ví dụ thực tế

### Trong form submit
```typescript
onSubmit() {
  this.categoryService.createCategory(this.categoryData).subscribe({
    next: (response) => {
      this.notificationService.success('Tạo danh mục thành công!');
      this.router.navigate(['/admin/categories']);
    },
    error: (error) => {
      this.notificationService.error('Không thể tạo danh mục. Vui lòng thử lại!');
      console.error(error);
    }
  });
}
```

### Trong delete action
```typescript
deleteCategory(id: number) {
  this.categoryService.deleteCategory(id).subscribe({
    next: () => {
      this.notificationService.success('Đã xóa danh mục thành công!');
      this.loadCategories();
    },
    error: (error) => {
      this.notificationService.error('Không thể xóa danh mục này!');
    }
  });
}
```

### Validation warning
```typescript
validateForm() {
  if (this.form.invalid) {
    this.notificationService.warning('Vui lòng điền đầy đủ thông tin!');
    return false;
  }
  return true;
}
```

## Thời gian hiển thị mặc định
- Success: 3000ms (3 giây)
- Error: 4000ms (4 giây)
- Warning: 3500ms (3.5 giây)
- Info: 3000ms (3 giây)

## Tính năng
- ✨ Tự động đóng sau thời gian xác định
- 🎨 Animation mượt mà khi hiển thị/ẩn
- 📱 Responsive trên mobile
- 🔘 Có nút đóng thủ công
- 📚 Hỗ trợ hiển thị nhiều thông báo cùng lúc
- 🎯 Hiển thị ở góc trên bên phải màn hình

