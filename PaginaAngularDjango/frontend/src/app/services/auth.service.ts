import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { BehaviorSubject, Observable, of, tap, catchError, map } from 'rxjs';
import { environment } from '../../environments/environment';

export interface TokenPair {
  access: string;
  refresh: string;
}

export interface Me {
  id: number;
  username: string;
  is_staff: boolean;
  is_superuser: boolean;
  groups: string[];
}

@Injectable({ providedIn: 'root' })
export class AuthService {
  private readonly baseUrl = environment.apiUrl;
  private readonly ACCESS_KEY = 'dp_access';
  private readonly REFRESH_KEY = 'dp_refresh';

  private loggedIn$ = new BehaviorSubject<boolean>(this.hasAccessToken());
  private me$ = new BehaviorSubject<Me | null>(null);

  constructor(private http: HttpClient) {}

  // ---- auth state ----
  isLoggedIn(): Observable<boolean> {
    return this.loggedIn$.asObservable();
  }

  hasAccessToken(): boolean {
    return !!localStorage.getItem(this.ACCESS_KEY);
  }

  getAccessToken(): string | null {
    return localStorage.getItem(this.ACCESS_KEY);
  }

  getRefreshToken(): string | null {
    return localStorage.getItem(this.REFRESH_KEY);
  }

  // ---- me / session ----
  initSession(): Observable<Me | null> {
    // si no hay token, sesión inválida
    if (!this.hasAccessToken()) {
      this.me$.next(null);
      this.loggedIn$.next(false);
      return of(null);
    }

    return this.http.get<Me>(`${this.baseUrl}/auth/me/`).pipe(
      tap((me) => {
        this.me$.next(me);
        this.loggedIn$.next(true);
      }),
      catchError(() => {
        // token malo/expirado o cualquier error -> logout “limpio”
        this.logout();
        return of(null);
      })
    );
  }

  getMeSnapshot(): Me | null {
    return this.me$.value;
  }

  hasAnyRole(roles: string[]): boolean {
    const me = this.getMeSnapshot();
    if (!me) return false;
    if (me.is_superuser) return true;
    const groups = me.groups ?? [];
    return roles.some((r) => groups.includes(r));
  }

  // ---- auth api ----
  login(username: string, password: string): Observable<TokenPair> {
    return this.http
      .post<TokenPair>(`${this.baseUrl}/auth/login/`, { username, password })
      .pipe(
        tap((tokens) => {
          localStorage.setItem(this.ACCESS_KEY, tokens.access);
          localStorage.setItem(this.REFRESH_KEY, tokens.refresh);
          this.loggedIn$.next(true);
        }),
        // después de login, trae /me para roles/navbar
        // (si falla, igual queda logueado pero sin roles cacheados)
        tap(() => {
          this.initSession().subscribe();
        })
      );
  }

  refresh(): Observable<{ access: string }> {
    const refresh = this.getRefreshToken();
    return this.http.post<{ access: string }>(`${this.baseUrl}/auth/refresh/`, {
      refresh: refresh ?? '',
    });
  }

  setAccessToken(access: string) {
    localStorage.setItem(this.ACCESS_KEY, access);
  }

  logout(): void {
    localStorage.removeItem(this.ACCESS_KEY);
    localStorage.removeItem(this.REFRESH_KEY);
    this.me$.next(null);
    this.loggedIn$.next(false);
  }
}