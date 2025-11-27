import {ActivatedRouteSnapshot, Router} from '@angular/router';
import {AuthService} from '../services/auth.service';
import {UserRole} from '../models/user.model';
import {inject} from '@angular/core';

export const roleGuard = (route: ActivatedRouteSnapshot) => {
  const authService = inject(AuthService);
  const router = inject(Router);
  const requiredRole = route.data['role'] as UserRole;

  if (authService.hasRole(requiredRole)) {
    return true;
  }

  const user = authService.getCurrentUser();
  if (user?.role === UserRole.CUSTOMER) {
    router.navigate(['/customer'])
  } else if (user?.role === UserRole.SHOP_OWNER) {
    router.navigate(['/shop-owner'])
  } else {
    router.navigate(['/login'])
  }
  return false;
}
