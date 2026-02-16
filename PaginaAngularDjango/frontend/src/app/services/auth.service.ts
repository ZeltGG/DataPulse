import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { BehaviorSubject, Observable, tap } from 'rxjs';
import { environment } from '../../environments/environment';

export interface TokenPair {
  access: string;
  refresh: string;
}

@Injectable({ providedIn: 'root' })
export class AuthService {
  private readonly baseUrl = environment.apiUrl;
  private readonly ACCESS_KEY = 'dp_access';
  private readonly REFRESH_KEY = 'dp_refresh';

  private loggedIn$ = new BehaviorSubject<boolean>(this.hasAccessToken());

  constructor(private http: HttpClient) {}

  // ---- state ----
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

  // ---- auth api ----
  login(username: string, password: string): Observable<TokenPair> {
    return this.http
      .post<TokenPair>(`${this.baseUrl}/auth/login/`, { username, password })
      .pipe(
        tap((tokens) => {
          localStorage.setItem(this.ACCESS_KEY, tokens.access);
          localStorage.setItem(this.REFRESH_KEY, tokens.refresh);
          this.loggedIn$.next(true);
        })
      );
  }

  refresh(): Observable<{ access: string }> {
    const refresh = this.getRefreshToken();
    if (!refresh) {
      // esto hará que el interceptor haga logout limpio si llega aquí
      return this.http.post<{ access: string }>(`${this.baseUrl}/auth/refresh/`, { refresh: '' });
    }
    return this.http.post<{ access: string }>(`${this.baseUrl}/auth/refresh/`, { refresh });
  }

  setAccessToken(access: string) {
    localStorage.setItem(this.ACCESS_KEY, access);
  }

  logout(): void {
    localStorage.removeItem(this.ACCESS_KEY);
    localStorage.removeItem(this.REFRESH_KEY);
    this.loggedIn$.next(false);
  }
}