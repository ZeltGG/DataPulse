import { Injectable } from '@angular/core';
import {
  HttpEvent,
  HttpHandler,
  HttpInterceptor,
  HttpRequest,
  HttpErrorResponse,
} from '@angular/common/http';
import { Observable, throwError, switchMap, catchError } from 'rxjs';
import { AuthService } from './auth.service';

@Injectable()
export class AuthInterceptor implements HttpInterceptor {
  private refreshing = false;

  constructor(private auth: AuthService) {}

  intercept(req: HttpRequest<any>, next: HttpHandler): Observable<HttpEvent<any>> {
    // No meter token en endpoints de auth
    const isAuthEndpoint =
      req.url.includes('/auth/login/') || req.url.includes('/auth/refresh/');

    const access = this.auth.getAccessToken();
    const authReq =
      !isAuthEndpoint && access
        ? req.clone({ setHeaders: { Authorization: `Bearer ${access}` } })
        : req;

    return next.handle(authReq).pipe(
      catchError((err: unknown) => {
        // Si no es HttpErrorResponse, re-lanzar
        if (!(err instanceof HttpErrorResponse)) return throwError(() => err);

        // Si 401 y tenemos refresh, intentar refresh 1 vez
        if (err.status === 401 && !isAuthEndpoint && this.auth.getRefreshToken()) {
          if (this.refreshing) {
            // Si ya hay refresh en curso, no spamear
            return throwError(() => err);
          }

          this.refreshing = true;

          return this.auth.refresh().pipe(
            switchMap((res) => {
              this.refreshing = false;
              this.auth.setAccessToken(res.access);

              const retryReq = req.clone({
                setHeaders: { Authorization: `Bearer ${res.access}` },
              });

              return next.handle(retryReq);
            }),
            catchError((e) => {
              this.refreshing = false;
              this.auth.logout();
              return throwError(() => e);
            })
          );
        }

        return throwError(() => err);
      })
    );
  }
}