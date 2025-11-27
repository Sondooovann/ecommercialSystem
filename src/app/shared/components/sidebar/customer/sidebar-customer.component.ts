import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';

interface SidebarItem {
  type: 'link' | 'checkbox' | 'range';
  label: string;
  value?: any;
  link?: string;
}

interface SidebarBox {
  title: string;
  items: SidebarItem[];
}

@Component({
  selector: 'jhi-sidebar-customer',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink],
  templateUrl: './sidebar-customer.component.html',
  styleUrls: ['./sidebar-customer.component.scss'],
})
export class SidebarCustomerComponent {
  @Input() boxes: SidebarBox[] = [];
  @Input() showRangeLabels = true;

  selectedValues: Record<string, boolean> = {};
  minPrice = 0;
  maxPrice = 1000;
}
