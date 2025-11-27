import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable } from 'rxjs';

interface Breadcrumb {
  label: string;
  url: string;
}

@Injectable({
  providedIn: 'root'
})
export class BreadcrumbService {
  private breadcrumbsSubject = new BehaviorSubject<Breadcrumb[]>([]);
  public breadcrumbs$: Observable<Breadcrumb[]> = this.breadcrumbsSubject.asObservable();

  setBreadcrumbs(breadcrumbs: Breadcrumb[]): void {
    this.breadcrumbsSubject.next(breadcrumbs);
  }

  addBreadcrumb(breadcrumb: Breadcrumb): void {
    const current = this.breadcrumbsSubject.value;
    this.breadcrumbsSubject.next([...current, breadcrumb]);
  }

  updateLastBreadcrumb(label: string): void {
    const current = [...this.breadcrumbsSubject.value];
    if (current.length > 0) {
      current[current.length - 1] = { ...current[current.length - 1], label };
      this.breadcrumbsSubject.next(current);
    }
  }

  clear(): void {
    this.breadcrumbsSubject.next([]);
  }
}

