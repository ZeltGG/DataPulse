import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { AuthService } from '../services/auth.service';
import { catchError, map, of } from 'rxjs';

export const authGuard: CanActivateFn = (route) => {
  const auth = inject(AuthService);
  const router = inject(Router);

  // Roles opcionales definidos en la ruta
  const allowed: string[] = (route.data?.['roles'] as string[]) ?? [];

  // 1) Si no hay token -> login
  if (!auth.hasAccessToken()) {
    router.navigateByUrl('/login');
    return false;
  }

  // 2) Si ya tenemos el usuario cargado (me), decidir rápido
  const me = auth.getMeSnapshot?.() ? auth.getMeSnapshot() : null;

  if (me) {
    // Si no se piden roles, basta estar logueado
    if (allowed.length === 0) return true;

    // Superuser pasa todo
    if (me.is_superuser) return true;

    const groups = me.groups ?? [];
    const ok = allowed.some((r) => groups.includes(r));
    if (!ok) router.navigateByUrl('/paises');
    return ok;
  }

  // 3) Si no hay "me" aún, pedir /auth/me y decidir
  return auth.initSession().pipe(
    map((meRes) => {
      if (!meRes) {
        router.navigateByUrl('/login');
        return false;
      }

      if (allowed.length === 0) return true;
      if (meRes.is_superuser) return true;

      const groups = meRes.groups ?? [];
      const ok = allowed.some((r) => groups.includes(r));
      if (!ok) router.navigateByUrl('/paises');
      return ok;
    }),
    catchError(() => {
      router.navigateByUrl('/login');
      return of(false);
    })
  );
};