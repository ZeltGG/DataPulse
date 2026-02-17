import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { catchError, map, of } from 'rxjs';
import { AuthService } from '../services/auth.service';

export const authGuard: CanActivateFn = () => {
  const auth = inject(AuthService);
  const router = inject(Router);

  if (!auth.hasAccessToken()) {
    router.navigateByUrl('/login');
    return false;
  }

  if (auth.getMeSnapshot()) {
    return true;
  }

  return auth.initSession().pipe(
    map((sessionMe) => {
      if (!sessionMe) {
        router.navigateByUrl('/login');
        return false;
      }
      return true;
    }),
    catchError(() => {
      router.navigateByUrl('/login');
      return of(false);
    })
  );
};
