import { Injectable } from '@angular/core';
import {
  HttpEvent,
  HttpHandler,
  HttpInterceptor,
  HttpRequest,
  HttpErrorResponse,
} from '@angular/common/http';
import { Observable, BehaviorSubject, throwError } from 'rxjs';
import { catchError, filter, switchMap, take, tap } from 'rxjs/operators';
import { AuthService } from './auth.service';

@Injectable()
export class AuthInterceptor implements HttpInterceptor {
  private refreshing = false;
  private refreshSubject = new BehaviorSubject<string | null>(null);

  constructor(private auth: AuthService) {}

  intercept(req: HttpRequest<any>, next: HttpHandler): Observable<HttpEvent<any>> {
    const isAuthEndpoint =
      req.url.includes('/auth/login/') || req.url.includes('/auth/refresh/');

    const access = this.auth.getAccessToken();
    const authReq =
      !isAuthEndpoint && access
        ? req.clone({ setHeaders: { Authorization: `Bearer ${access}` } })
        : req;

    return next.handle(authReq).pipe(
      catchError((err: unknown) => {
        if (!(err instanceof HttpErrorResponse)) return throwError(() => err);

        // solo intentamos refresh si es 401, no es endpoint de auth, y hay refresh token
        if (err.status === 401 && !isAuthEndpoint && this.auth.getRefreshToken()) {
          return this.handle401(req, next);
        }

        return throwError(() => err);
      })
    );
  }

  private handle401(req: HttpRequest<any>, next: HttpHandler) {
    // Si ya está refrescando, esperar a que llegue el nuevo access
    if (this.refreshing) {
      return this.refreshSubject.pipe(
        filter((t): t is string => !!t),
        take(1),
        switchMap((newAccess) => {
          const retryReq = req.clone({
            setHeaders: { Authorization: `Bearer ${newAccess}` },
          });
          return next.handle(retryReq);
        })
      );
    }

    this.refreshing = true;
    this.refreshSubject.next(null);

    return this.auth.refresh().pipe(
      tap((res) => {
        this.auth.setAccessToken(res.access);
        this.refreshing = false;
        this.refreshSubject.next(res.access);
      }),
      switchMap((res) => {
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
}