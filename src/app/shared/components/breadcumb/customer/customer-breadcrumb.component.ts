import { Component, OnInit } from '@angular/core';
import {Router, ActivatedRoute, NavigationEnd, RouterModule} from '@angular/router';
import { CommonModule } from '@angular/common';
import { filter } from 'rxjs/operators';
import { BreadcrumbService } from '../../../../core/services/breadcrumb.service';

interface Breadcrumb {
  label: string;
  url: string;
}

@Component({
  selector: 'jhi-customer-breadcrumb',
  standalone: true,
  imports: [CommonModule, RouterModule],
  templateUrl: './customer-breadcrumb.component.html',
  styleUrls: ['./customer-breadcrumb.component.scss']
})
export class CustomerBreadcrumbComponent implements OnInit {
  breadcrumbs: Breadcrumb[] = [];

  constructor(
    private router: Router, 
    private route: ActivatedRoute,
    private breadcrumbService: BreadcrumbService
  ) {
    this.router.events
      .pipe(filter(event => event instanceof NavigationEnd))
      .subscribe(() => {
        const breadcrumbs = this.buildBreadcrumb(this.route.root);
        this.breadcrumbService.setBreadcrumbs(breadcrumbs);
      });

    // Subscribe to breadcrumb updates
    this.breadcrumbService.breadcrumbs$.subscribe(breadcrumbs => {
      this.breadcrumbs = breadcrumbs;
    });
  }

  ngOnInit(): void {
    const breadcrumbs = this.buildBreadcrumb(this.route.root);
    this.breadcrumbService.setBreadcrumbs(breadcrumbs);
  }

  private buildBreadcrumb(route: ActivatedRoute, url: string = '', breadcrumbs: Breadcrumb[] = []): Breadcrumb[] {
    const children = route.children;

    if (children.length === 0) return breadcrumbs;

    for (let child of children) {
      const routeURL: string = child.snapshot.url.map(segment => segment.path).join('/');
      if (routeURL !== '') url += `/${routeURL}`;

      const label = child.snapshot.data['breadcrumb'];
      if (label) breadcrumbs.push({ label, url });

      return this.buildBreadcrumb(child, url, breadcrumbs);
    }

    return breadcrumbs;
  }
}
