import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { map } from 'rxjs';

import { UserService } from './user.service';

export const adminGuard: CanActivateFn = () => {
  const userService = inject(UserService);
  const router = inject(Router);

  return userService.me().pipe(
    map((user) => {
      const isAdmin = (user.roles || []).includes('administradores');
      if (!isAdmin) {
        router.navigate(['/dashboard']);
        return false;
      }
      return true;
    })
  );
};
