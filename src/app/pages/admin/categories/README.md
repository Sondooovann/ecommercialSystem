# Quản lý Danh mục (Category Management)

## Tổng quan

Module quản lý danh mục cho phép admin tạo, xem, chỉnh sửa và xóa các danh mục sản phẩm. Hỗ trợ cấu trúc phân cấp với danh mục cha và danh mục con.

## Cấu trúc file

```
categories/
├── category-list/
│   ├── admin-category-list.component.ts     # Component logic
│   ├── admin-category-list.component.html   # Template
│   └── admin-category-list.component.scss   # Styles
└── README.md
```

## API Endpoints

### 1. Lấy danh sách danh mục
```
GET http://localhost:8000/api/products/categories/
```

**Response:**
```json
{
  "success": true,
  "data": {
    "status": "success",
    "message": "Đã lấy danh sách danh mục thành công",
    "data": [
      {
        "id": 1,
        "name": "Quần áo",
        "image": null,
        "status": "active",
        "parent": null
      }
    ]
  },
  "message": "Thành công"
}
```

### 2. Tạo danh mục mới
```
POST http://localhost:8000/api/products/categories/create/
```

**Request Body:**
```json
{
  "name": "Tên danh mục",
  "description": "Mô tả",
  "is_active": true,
  "parent": "",  // ID của danh mục cha hoặc empty string
  "image": null  // File upload (optional)
}
```

### 3. Cập nhật danh mục
```
PUT http://localhost:8000/api/products/categories/{id}/update/
```

**Request Body:** Tương tự như create

### 4. Xóa danh mục
```
DELETE http://localhost:8000/api/products/categories/{id}/delete/
```

**Lưu ý:** Không thể xóa danh mục có danh mục con

## Tính năng

### 1. Hiển thị danh sách
- ✅ Hiển thị tất cả danh mục
- ✅ Chế độ xem dạng bảng (table) - danh sách phẳng
- ✅ Chế độ xem dạng cây (tree) - hiển thị cấu trúc phân cấp
- ✅ Expand/Collapse từng node trong tree view
- ✅ Nút "Mở rộng tất cả" / "Thu gọn tất cả"
- ✅ Icons folder đặc biệt cho danh mục cha/con
- ✅ Visual tree với branch lines và indentation
- ✅ Hiển thị thông tin: ID, tên, danh mục cha, số danh mục con, trạng thái

### 2. Tìm kiếm & Lọc
- ✅ Tìm kiếm theo tên danh mục
- ✅ Lọc theo trạng thái (Tất cả, Hoạt động, Không hoạt động)
- ✅ Chuyển đổi giữa chế độ xem bảng và cây

### 3. Thêm mới danh mục
- ✅ Modal form để tạo danh mục mới
- ✅ Các trường: Tên*, Mô tả, Danh mục cha, Hình ảnh, Trạng thái
- ✅ Validation: Tên là bắt buộc
- ✅ Có thể chọn danh mục cha để tạo cấu trúc phân cấp

### 4. Chỉnh sửa danh mục
- ✅ Modal form để chỉnh sửa
- ✅ Load dữ liệu hiện tại của danh mục
- ✅ Validation giống như tạo mới

### 5. Xóa danh mục
- ✅ Xác nhận trước khi xóa
- ✅ Kiểm tra danh mục con trước khi xóa
- ✅ Hiển thị thông báo nếu không thể xóa

## Cách sử dụng

### Truy cập module
Vào menu Admin → **Danh mục** hoặc truy cập URL: `/admin/categories`

### Thêm danh mục mới
1. Click nút **"Thêm danh mục"**
2. Điền thông tin:
   - **Tên danh mục** (bắt buộc)
   - **Mô tả** (tùy chọn)
   - **Danh mục cha** (tùy chọn - để trống nếu là danh mục gốc)
   - **Hình ảnh** (tùy chọn)
   - **Trạng thái hoạt động** (checkbox)
3. Click **"Tạo mới"**

### Chỉnh sửa danh mục
1. Click icon **Edit** (✏️) trên hàng danh mục cần sửa
2. Cập nhật thông tin trong modal
3. Click **"Cập nhật"**

### Xóa danh mục
1. Click icon **Delete** (🗑️) trên hàng danh mục cần xóa
2. Xác nhận xóa trong dialog
3. **Lưu ý:** Không thể xóa nếu còn danh mục con

### Chuyển đổi chế độ xem
- Click nút **"Hiển thị dạng cây"** / **"Hiển thị dạng bảng"**
- **Dạng bảng:** Hiển thị danh sách phẳng, dễ quét
- **Dạng cây:** Hiển thị cấu trúc phân cấp rõ ràng với:
  - Icons mũi tên để expand/collapse từng node
  - Folder icons màu cam cho danh mục cha
  - Tree branch lines để thể hiện quan hệ
  - Gradient header đẹp mắt
  - Badge đếm số danh mục con

### Expand/Collapse trong Tree View
1. **Click vào mũi tên** bên cạnh danh mục để mở rộng/thu gọn
2. **Click "Mở rộng tất cả"** để mở tất cả các node cha
3. **Click "Thu gọn tất cả"** để đóng tất cả các node
4. Mặc định: tất cả danh mục cha được mở rộng khi load trang

### Tìm kiếm & Lọc
1. Nhập từ khóa vào ô tìm kiếm và Enter hoặc click "Tìm kiếm"
2. Chọn trạng thái từ dropdown để lọc
3. Kết quả sẽ tự động cập nhật

## Models

### Category Model
```typescript
interface Category {
  id: number;
  name: string;
  image: string | null;
  status: string;         // 'active' | 'inactive'
  parent: number | null;  // ID của danh mục cha
  description?: string;
}
```

### Category Create/Update Request
```typescript
interface CategoryCreateRequest {
  name: string;
  description?: string;
  is_active: boolean;
  parent: string | number;  // Empty string hoặc ID
  image?: File | null;
}
```

## Services

### CategoryService
- `getCategories()`: Lấy danh sách tất cả danh mục
- `getCategoryById(id)`: Lấy thông tin chi tiết 1 danh mục
- `createCategory(data)`: Tạo danh mục mới
- `updateCategory(id, data)`: Cập nhật danh mục
- `deleteCategory(id)`: Xóa danh mục
- `buildCategoryTree(categories)`: Xây dựng cấu trúc cây từ danh sách
- `getParentCategories(categories)`: Lấy danh sách danh mục gốc
- `getChildCategories(categories, parentId)`: Lấy danh mục con

## Responsive Design

- ✅ Desktop: Hiển thị đầy đủ tính năng
- ✅ Tablet: Tối ưu layout
- ✅ Mobile: Responsive menu, modal fullscreen

## Styling

Component sử dụng CSS Variables cho theming:
- `--primary-color`: Màu chủ đạo (mặc định: #2d5016)
- Tất cả màu sắc, spacing tuân theo design system chung

## Lưu ý kỹ thuật

1. **Cấu trúc phân cấp:**
   - Hỗ trợ 1 cấp cha-con
   - Parent = null: danh mục gốc
   - Parent = ID: danh mục con

2. **Validation:**
   - Không thể xóa danh mục có con
   - Không thể chọn chính mình làm parent khi edit

3. **Form data:**
   - Sử dụng FormData để upload file
   - Convert is_active từ boolean sang string khi gửi API

4. **Tree rendering:**
   - Flatten tree để dễ render trong table
   - Sử dụng margin-left để tạo indent
   - Hiển thị ký tự └─ cho danh mục con

## Troubleshooting

### API không trả về dữ liệu
- Kiểm tra backend có chạy không
- Kiểm tra CORS settings
- Xem console log để debug

### Không thể upload ảnh
- Kiểm tra backend có hỗ trợ multipart/form-data không
- Kiểm tra file size limit
- Kiểm tra format file được accept

### Modal không hiển thị
- Kiểm tra `showModal` flag
- Xem console có lỗi JS không
- Clear cache và reload

## Cải tiến trong tương lai

- [ ] Drag & drop để sắp xếp thứ tự
- [ ] Bulk actions (xóa nhiều cùng lúc)
- [ ] Export/Import danh mục
- [ ] Hỗ trợ đa cấp độ (nested categories)
- [ ] Preview hình ảnh trước khi upload
- [ ] Crop/resize ảnh trước khi upload
- [ ] SEO fields (slug, meta description)

