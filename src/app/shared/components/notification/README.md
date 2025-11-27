# 🔔 Notification System - Hệ thống thông báo

## 📋 Tổng quan

Hệ thống thông báo toast hiện đại cho ứng dụng Angular, hiển thị thông báo ở góc trên bên phải màn hình với animation mượt mà và tự động đóng.

## ✨ Tính năng

- ✅ **4 loại thông báo**: Success, Error, Warning, Info
- 🎨 **Animation mượt mà**: Slide in/out từ bên phải
- ⏱️ **Tự động đóng**: Sau thời gian xác định (có thể tùy chỉnh)
- 🔘 **Đóng thủ công**: Nút X để đóng ngay lập tức
- 📚 **Nhiều thông báo**: Hiển thị nhiều thông báo cùng lúc (xếp chồng)
- 📱 **Responsive**: Tự động điều chỉnh trên mobile
- 🎯 **Vị trí cố định**: Luôn ở góc trên bên phải
- 🌈 **Theme đẹp mắt**: Màu sắc và icon phù hợp với từng loại

## 📁 Cấu trúc file

```
src/app/
├── core/
│   └── services/
│       └── notification.service.ts    # Service quản lý thông báo
├── shared/
│   ├── models/
│   │   └── notification.model.ts      # Model cho notification
│   └── components/
│       └── notification/
│           ├── notification.component.ts
│           ├── notification.component.html
│           ├── notification.component.scss
│           ├── USAGE.md               # Hướng dẫn chi tiết
│           └── README.md              # File này
└── app.component.html                 # Đã thêm <app-notification>
```

## 🚀 Cài đặt

Hệ thống đã được cài đặt và cấu hình sẵn, bạn chỉ cần sử dụng!

### Dependencies đã được thêm:
- `@angular/animations`: ^19.2.0

### Config đã được cập nhật:
- `app.config.ts`: Đã thêm `provideAnimations()`
- `app.component.html`: Đã thêm `<app-notification></app-notification>`
- `app.component.ts`: Đã import `NotificationComponent`

## 📖 Cách sử dụng nhanh

### 1. Import service vào component

```typescript
import { NotificationService } from '../../../core/services/notification.service';

export class YourComponent {
  constructor(private notificationService: NotificationService) {}
}
```

### 2. Sử dụng trong code

```typescript
// Thông báo thành công
this.notificationService.success('Lưu dữ liệu thành công!');

// Thông báo lỗi
this.notificationService.error('Có lỗi xảy ra!');

// Thông báo cảnh báo
this.notificationService.warning('Vui lòng kiểm tra lại!');

// Thông báo thông tin
this.notificationService.info('Đang xử lý...');
```

## 🎨 Các loại thông báo

| Loại | Method | Màu sắc | Icon | Thời gian mặc định |
|------|--------|---------|------|-------------------|
| Success | `success()` | Xanh lá | ✓ | 3000ms (3s) |
| Error | `error()` | Đỏ | ✗ | 4000ms (4s) |
| Warning | `warning()` | Vàng | ⚠ | 3500ms (3.5s) |
| Info | `info()` | Xanh dương | ℹ | 3000ms (3s) |

## 💡 Ví dụ thực tế

### Trong form submit
```typescript
onSubmit() {
  if (this.form.invalid) {
    this.notificationService.warning('Vui lòng điền đầy đủ thông tin!');
    return;
  }

  this.apiService.create(this.formData).subscribe({
    next: (response) => {
      this.notificationService.success('Tạo mới thành công!');
      this.router.navigate(['/list']);
    },
    error: (error) => {
      this.notificationService.error('Không thể tạo mới. Vui lòng thử lại!');
    }
  });
}
```

### Trong delete action
```typescript
deleteItem(id: number) {
  if (confirm('Bạn có chắc chắn muốn xóa?')) {
    this.apiService.delete(id).subscribe({
      next: () => {
        this.notificationService.success('Đã xóa thành công!');
        this.loadData();
      },
      error: () => {
        this.notificationService.error('Không thể xóa. Vui lòng thử lại!');
      }
    });
  }
}
```

### Với thời gian tùy chỉnh
```typescript
// Hiển thị 5 giây
this.notificationService.success('Đã lưu thành công!', 5000);

// Hiển thị 10 giây
this.notificationService.error('Lỗi nghiêm trọng!', 10000);
```

## 🛠️ API Reference

### NotificationService

#### Methods

##### `success(message: string, duration?: number): void`
Hiển thị thông báo thành công
- **message**: Nội dung thông báo
- **duration**: Thời gian hiển thị (ms), mặc định 3000ms

##### `error(message: string, duration?: number): void`
Hiển thị thông báo lỗi
- **message**: Nội dung thông báo
- **duration**: Thời gian hiển thị (ms), mặc định 4000ms

##### `warning(message: string, duration?: number): void`
Hiển thị thông báo cảnh báo
- **message**: Nội dung thông báo
- **duration**: Thời gian hiển thị (ms), mặc định 3500ms

##### `info(message: string, duration?: number): void`
Hiển thị thông báo thông tin
- **message**: Nội dung thông báo
- **duration**: Thời gian hiển thị (ms), mặc định 3000ms

##### `remove(id: string): void`
Xóa thông báo theo ID (thường dùng nội bộ)

##### `clear(): void`
Xóa tất cả thông báo đang hiển thị

## 🎯 Best Practices

### ✅ Nên làm
- Sử dụng thông báo success sau các action thành công
- Sử dụng error cho lỗi API hoặc validation
- Sử dụng warning cho cảnh báo không nghiêm trọng
- Sử dụng info cho thông tin cập nhật hoặc loading
- Giữ message ngắn gọn, rõ ràng
- Sử dụng tiếng Việt có dấu cho dễ đọc

### ❌ Không nên làm
- Không hiển thị quá nhiều thông báo cùng lúc
- Không đặt duration quá ngắn (< 2000ms)
- Không đặt duration quá dài (> 10000ms)
- Không dùng cho các message quá dài
- Không thay thế confirm dialog bằng notification

## 📱 Responsive

Notification tự động điều chỉnh trên các thiết bị:
- **Desktop**: Hiển thị ở góc trên phải, max-width 400px
- **Mobile**: Full width với margin 20px hai bên

## 🎨 Customization

Nếu muốn tùy chỉnh style, edit file:
```
src/app/shared/components/notification/notification.component.scss
```

Các biến có thể tùy chỉnh:
- Màu sắc cho từng loại thông báo
- Kích thước, padding, border-radius
- Animation duration
- Box shadow
- Font size

## 📝 Demo Component

Xem ví dụ sử dụng thực tế trong:
```
src/app/pages/admin/categories/category-list/admin-category-list.component.ts
```

Component này đã được cập nhật để sử dụng NotificationService thay vì `alert()`.

## 🐛 Troubleshooting

### Thông báo không hiển thị?
1. Kiểm tra `<app-notification></app-notification>` đã được thêm vào `app.component.html`
2. Kiểm tra `provideAnimations()` đã được thêm vào `app.config.ts`
3. Kiểm tra `@angular/animations` đã được cài đặt

### Animation không hoạt động?
- Đảm bảo `provideAnimations()` đã được thêm vào providers

### Z-index bị che?
- Notification có z-index: 9999, nếu vẫn bị che, tăng giá trị này trong SCSS

## 📚 Tài liệu thêm

- [Angular Animations](https://angular.dev/guide/animations)
- [RxJS BehaviorSubject](https://rxjs.dev/api/index/class/BehaviorSubject)
- [Bootstrap Icons](https://icons.getbootstrap.com/)

## 🤝 Đóng góp

Nếu có ý tưởng cải thiện, hãy thảo luận với team!

---

Made with ❤️ for ECommercial FrontEnd

