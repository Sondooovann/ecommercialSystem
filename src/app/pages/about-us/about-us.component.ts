import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';

interface Milestone {
  year: string;
  title: string;
  description: string;
}

interface Value {
  icon: string;
  title: string;
  description: string;
}

@Component({
  selector: 'jhi-about-us',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './about-us.component.html',
  styleUrls: ['./about-us.component.scss']
})
export class AboutUsComponent {
  milestones: Milestone[] = [
    {
      year: '2003',
      title: 'Khởi Nghiệp',
      description: 'Thành lập doanh nghiệp với mô hình nhỏ, tập trung vào chất lượng sản phẩm chè Thái Nguyên'
    },
    {
      year: '2008',
      title: 'Mở Rộng',
      description: 'Mở rộng quy mô sản xuất, hợp tác với nhiều hợp tác xã trồng chè tại Tân Cương'
    },
    {
      year: '2013',
      title: 'Phát Triển',
      description: 'Ra mắt thương hiệu Thái Nguyên Xanh, đưa sản phẩm vào hệ thống siêu thị lớn'
    },
    {
      year: '2018',
      title: 'Đổi Mới',
      description: 'Ứng dụng công nghệ hiện đại vào quy trình chế biến, nâng cao chất lượng sản phẩm'
    },
    {
      year: '2023',
      title: 'Bứt Phá',
      description: 'Mở rộng thị trường online, xuất khẩu sản phẩm chè ra thị trường quốc tế'
    }
  ];

  values: Value[] = [
    {
      icon: '🌱',
      title: 'Chất Lượng',
      description: 'Cam kết 100% sản phẩm chè tự nhiên, không chất bảo quản, đạt tiêu chuẩn an toàn thực phẩm'
    },
    {
      icon: '💚',
      title: 'Uy Tín',
      description: 'Xây dựng niềm tin với khách hàng thông qua chất lượng sản phẩm và dịch vụ tận tâm'
    },
    {
      icon: '🤝',
      title: 'Trách Nhiệm',
      description: 'Hỗ trợ người trồng chè địa phương, đóng góp vào phát triển kinh tế bền vững'
    },
    {
      icon: '🎯',
      title: 'Đổi Mới',
      description: 'Không ngừng cải tiến, áp dụng công nghệ mới để nâng cao chất lượng sản phẩm'
    }
  ];

  constructor(private router: Router) {}

  goToProducts(): void {
    this.router.navigate(['/buyer/product']);
  }

  goToAgency(): void {
    this.router.navigate(['/buyer/agency']);
  }
}

