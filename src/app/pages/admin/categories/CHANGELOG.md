# Changelog - Quản lý Danh mục

## [1.1.0] - 2024-11-17

### ✨ Added - Cải tiến Tree View
- **Expand/Collapse Functionality**: Có thể mở rộng và thu gọn từng node trong tree view
- **Nút điều khiển**: Thêm nút "Mở rộng tất cả" và "Thu gọn tất cả"
- **Visual Enhancement**:
  - Gradient header đẹp mắt cho tree table (purple gradient)
  - Folder icons màu cam cho danh mục cha
  - Folder icons xám cho danh mục con
  - Tree branch lines để hiển thị quan hệ cha-con
  - Badge gradient đếm số danh mục con
  - Expand/collapse buttons với hover effect
  
### 🎨 Improved
- Mặc định hiển thị dạng cây thay vì dạng bảng
- Tự động mở rộng tất cả danh mục cha khi load trang
- Hover effects cho các nút và icons
- Responsive design cho mobile với icons nhỏ hơn

### 🐛 Fixed
- Cải thiện padding và spacing trong tree view
- Tối ưu hiển thị trên mobile

---

## [1.0.0] - 2024-11-17

### ✨ Initial Release
- Hiển thị danh sách danh mục
- Chế độ xem dạng bảng và dạng cây
- Tìm kiếm theo tên
- Lọc theo trạng thái
- Thêm mới danh mục
- Chỉnh sửa danh mục
- Xóa danh mục (với validation)
- Upload hình ảnh
- Hỗ trợ cấu trúc phân cấp (parent-child)
- Modal form responsive
- Validation đầy đủ

### 📝 Features
- Full CRUD operations
- Category Service với API integration
- Tree structure builder
- Responsive design
- Error handling
- Loading states

