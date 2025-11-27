import {AuthService} from '../services/auth.service';
import {Router} from '@angular/router';
import {inject} from '@angular/core';

export const authGuard = () => {
  const authService = inject(AuthService);
  const router = inject(Router);

  if (authService.isAuthenticated()) {
    return true;
  }
  router.navigate(['/login']);
  return false;
}
