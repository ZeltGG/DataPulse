import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { catchError, map, of } from 'rxjs';
import { AuthService } from '../services/auth.service';

export const authGuard: CanActivateFn = (route) => {
  const auth = inject(AuthService);
  const router = inject(Router);

  if (!auth.hasAccessToken()) {
    router.navigateByUrl('/login');
    return false;
  }

  const allowedRoles = (route.data?.['roles'] as string[] | undefined) || [];
  const me = auth.getMeSnapshot();

  if (me) {
    if (!allowedRoles.length || auth.hasRole(...allowedRoles)) {
      return true;
    }
    router.navigateByUrl('/paises');
    return false;
  }

  return auth.initSession().pipe(
    map((sessionMe) => {
      if (!sessionMe) {
        router.navigateByUrl('/login');
        return false;
      }

      if (!allowedRoles.length || auth.hasRole(...allowedRoles)) {
        return true;
      }

      router.navigateByUrl('/paises');
      return false;
    }),
    catchError(() => {
      router.navigateByUrl('/login');
      return of(false);
    })
  );
};
