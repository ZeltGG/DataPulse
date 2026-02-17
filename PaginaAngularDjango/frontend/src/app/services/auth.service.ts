import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { BehaviorSubject, Observable, catchError, map, of, tap } from 'rxjs';
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
  private readonly ME_KEY = 'dp_me';

  private loggedIn$ = new BehaviorSubject<boolean>(this.hasAccessToken());
  private me$ = new BehaviorSubject<Me | null>(this.loadMeFromStorage());

  constructor(private http: HttpClient) {}

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

  me(): Observable<Me> {
    return this.http.get<Me>(`${this.baseUrl}/auth/me/`).pipe(
      tap((me) => {
        this.me$.next(me);
        localStorage.setItem(this.ME_KEY, JSON.stringify(me));
        this.loggedIn$.next(true);
      })
    );
  }

  initSession(): Observable<Me | null> {
    if (!this.hasAccessToken()) {
      this.clearSession();
      return of(null);
    }

    return this.me().pipe(
      map((me) => me as Me | null),
      catchError(() => {
        this.logout();
        return of(null);
      })
    );
  }

  getMeSnapshot(): Me | null {
    return this.me$.value;
  }

  hasRole(...roles: string[]): boolean {
    const me = this.getMeSnapshot();
    if (!me) {
      return false;
    }
    if (me.is_superuser) {
      return true;
    }
    if (!roles.length) {
      return false;
    }
    const groups = me.groups || [];
    return roles.some((role) => groups.includes(role));
  }

  isAdmin(): boolean {
    const me = this.getMeSnapshot();
    if (!me) {
      return false;
    }
    return me.is_superuser || this.hasRole('ADMIN');
  }

  login(username: string, password: string): Observable<TokenPair> {
    return this.http.post<TokenPair>(`${this.baseUrl}/auth/login/`, { username, password }).pipe(
      tap((tokens) => {
        localStorage.setItem(this.ACCESS_KEY, tokens.access);
        localStorage.setItem(this.REFRESH_KEY, tokens.refresh);
        this.loggedIn$.next(true);
      })
    );
  }

  refresh(): Observable<{ access: string }> {
    const refresh = this.getRefreshToken();
    return this.http.post<{ access: string }>(`${this.baseUrl}/auth/refresh/`, {
      refresh: refresh ?? '',
    });
  }

  setAccessToken(access: string): void {
    localStorage.setItem(this.ACCESS_KEY, access);
    this.loggedIn$.next(true);
  }

  logout(): void {
    this.clearSession();
  }

  private loadMeFromStorage(): Me | null {
    const raw = localStorage.getItem(this.ME_KEY);
    if (!raw) {
      return null;
    }

    try {
      return JSON.parse(raw) as Me;
    } catch {
      localStorage.removeItem(this.ME_KEY);
      return null;
    }
  }

  private clearSession(): void {
    localStorage.removeItem(this.ACCESS_KEY);
    localStorage.removeItem(this.REFRESH_KEY);
    localStorage.removeItem(this.ME_KEY);
    this.me$.next(null);
    this.loggedIn$.next(false);
  }
}
