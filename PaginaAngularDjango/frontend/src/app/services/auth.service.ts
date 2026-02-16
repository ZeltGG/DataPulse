import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { BehaviorSubject, Observable, of, tap, catchError, map } from 'rxjs';
import { environment } from '../../environments/environment';

export interface TokenPair {
  access: string;
  refresh: string;
}

export interface MeResponse {
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
  private me$ = new BehaviorSubject<MeResponse | null>(null);

  constructor(private http: HttpClient) {}

  // ---------------- state ----------------
  isLoggedIn(): Observable<boolean> {
    return this.loggedIn$.asObservable();
  }

  me(): Observable<MeResponse | null> {
    return this.me$.asObservable();
  }

  getMeSnapshot(): MeResponse | null {
    return this.me$.value;
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

  // Helpers de rol
  hasRole(role: string): boolean {
    const u = this.me$.value;
    if (!u) return false;
    if (u.is_superuser) return true;
    return (u.groups || []).includes(role);
  }

  isAdmin(): boolean {
    // si tu grupo se llama "ADMIN"
    return this.hasRole('ADMIN') || this.getMeSnapshot()?.is_staff === true;
  }

  // Llamar al arrancar la app (si hay token) para “hidratar” roles
  initSession(): Observable<MeResponse | null> {
    if (!this.hasAccessToken()) {
      this.me$.next(null);
      this.loggedIn$.next(false);
      return of(null);
    }

    return this.http.get<MeResponse>(`${this.baseUrl}/auth/me/`).pipe(
      tap((me) => {
        this.me$.next(me);
        this.loggedIn$.next(true);
      }),
      catchError(() => {
        // token inválido / expirado
        this.logout();
        return of(null);
      })
    );
  }

  // ---------------- auth api ----------------
  login(username: string, password: string): Observable<TokenPair> {
    return this.http
      .post<TokenPair>(`${this.baseUrl}/auth/login/`, { username, password })
      .pipe(
        tap((tokens) => {
          localStorage.setItem(this.ACCESS_KEY, tokens.access);
          localStorage.setItem(this.REFRESH_KEY, tokens.refresh);
          this.loggedIn$.next(true);
        }),
        // luego pedimos /me para conocer grupos/roles
        // (esto evita que el navbar/guards dependan “a ciegas”)
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