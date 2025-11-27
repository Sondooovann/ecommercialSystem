import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

interface Agency {
  id: number;
  name: string;
  address: string;
  phone: string;
  email: string;
  city: string;
  region: 'north' | 'central' | 'south';
  image?: string;
}

interface Benefit {
  icon: string;
  title: string;
  description: string;
}

@Component({
  selector: 'jhi-agency',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './agency.component.html',
  styleUrls: ['./agency.component.scss']
})
export class AgencyComponent {
  selectedRegion: string = 'all';
  searchText: string = '';

  agencies: Agency[] = [
    {
      id: 1,
      name: 'Đại Lý Chè Thái Nguyên Xanh - Hà Nội',
      address: '123 Phố Huế, Quận Hai Bà Trưng, Hà Nội',
      phone: '024.3456.7890',
      email: 'hanoi@thainguyenxanh.vn',
      city: 'Hà Nội',
      region: 'north'
    },
    {
      id: 2,
      name: 'Đại Lý Chè Thái Nguyên Xanh - Thái Nguyên',
      address: '456 Đường Lương Ngọc Quyến, TP. Thái Nguyên',
      phone: '0208.3654.789',
      email: 'thainguyen@thainguyenxanh.vn',
      city: 'Thái Nguyên',
      region: 'north'
    },
    {
      id: 3,
      name: 'Đại Lý Chè Thái Nguyên Xanh - Hải Phòng',
      address: '789 Lê Lợi, Quận Ngô Quyền, Hải Phòng',
      phone: '0225.3654.789',
      email: 'haiphong@thainguyenxanh.vn',
      city: 'Hải Phòng',
      region: 'north'
    },
    {
      id: 4,
      name: 'Đại Lý Chè Thái Nguyên Xanh - Đà Nẵng',
      address: '321 Nguyễn Văn Linh, Quận Thanh Khê, Đà Nẵng',
      phone: '0236.3654.789',
      email: 'danang@thainguyenxanh.vn',
      city: 'Đà Nẵng',
      region: 'central'
    },
    {
      id: 5,
      name: 'Đại Lý Chè Thái Nguyên Xanh - Huế',
      address: '654 Lê Duẩn, TP. Huế',
      phone: '0234.3654.789',
      email: 'hue@thainguyenxanh.vn',
      city: 'Huế',
      region: 'central'
    },
    {
      id: 6,
      name: 'Đại Lý Chè Thái Nguyên Xanh - TP. Hồ Chí Minh',
      address: '987 Nguyễn Trãi, Quận 1, TP. Hồ Chí Minh',
      phone: '028.3654.7890',
      email: 'hcm@thainguyenxanh.vn',
      city: 'TP. Hồ Chí Minh',
      region: 'south'
    },
    {
      id: 7,
      name: 'Đại Lý Chè Thái Nguyên Xanh - Cần Thơ',
      address: '147 Nguyễn Văn Cừ, Quận Ninh Kiều, Cần Thơ',
      phone: '0292.3654.789',
      email: 'cantho@thainguyenxanh.vn',
      city: 'Cần Thơ',
      region: 'south'
    },
    {
      id: 8,
      name: 'Đại Lý Chè Thái Nguyên Xanh - Biên Hòa',
      address: '258 Võ Thị Sáu, TP. Biên Hòa, Đồng Nai',
      phone: '0251.3654.789',
      email: 'bienhoa@thainguyenxanh.vn',
      city: 'Biên Hòa',
      region: 'south'
    }
  ];

  benefits: Benefit[] = [
    {
      icon: '💰',
      title: 'Giá Ưu Đãi',
      description: 'Chính sách giá tốt nhất cho đại lý, hỗ trợ chiết khấu hấp dẫn'
    },
    {
      icon: '📦',
      title: 'Hỗ Trợ Kho Hàng',
      description: 'Đảm bảo nguồn hàng ổn định, giao hàng nhanh chóng'
    },
    {
      icon: '📈',
      title: 'Marketing',
      description: 'Hỗ trợ vật liệu marketing, tư vấn kinh doanh hiệu quả'
    },
    {
      icon: '🎓',
      title: 'Đào Tạo',
      description: 'Đào tạo kiến thức về sản phẩm và kỹ năng bán hàng'
    }
  ];

  get filteredAgencies(): Agency[] {
    let filtered = this.agencies;

    // Filter by region
    if (this.selectedRegion !== 'all') {
      filtered = filtered.filter(agency => agency.region === this.selectedRegion);
    }

    // Filter by search text
    if (this.searchText.trim()) {
      const searchLower = this.searchText.toLowerCase();
      filtered = filtered.filter(agency =>
        agency.name.toLowerCase().includes(searchLower) ||
        agency.city.toLowerCase().includes(searchLower) ||
        agency.address.toLowerCase().includes(searchLower)
      );
    }

    return filtered;
  }

  getRegionName(region: string): string {
    const regionMap: { [key: string]: string } = {
      'north': 'Miền Bắc',
      'central': 'Miền Trung',
      'south': 'Miền Nam'
    };
    return regionMap[region] || region;
  }

  selectRegion(region: string): void {
    this.selectedRegion = region;
  }

  clearSearch(): void {
    this.searchText = '';
  }
}

