import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { BehaviorSubject, Observable, tap } from 'rxjs';
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
  private readonly ME_KEY = 'dp_me';

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
    // Si no hay refresh, mandamos vacío para que falle limpio y el interceptor haga logout
    return this.http.post<{ access: string }>(`${this.baseUrl}/auth/refresh/`, {
      refresh: refresh ?? '',
    });
  }

  setAccessToken(access: string): void {
    localStorage.setItem(this.ACCESS_KEY, access);
  }

  // ---- me / roles ----
  me(): Observable<MeResponse> {
    return this.http.get<MeResponse>(`${this.baseUrl}/auth/me/`).pipe(
      tap((me) => localStorage.setItem(this.ME_KEY, JSON.stringify(me)))
    );
  }

  getMeCached(): MeResponse | null {
    const raw = localStorage.getItem(this.ME_KEY);
    return raw ? (JSON.parse(raw) as MeResponse) : null;
  }

  hasGroup(groupName: string): boolean {
    const me = this.getMeCached();
    return !!me?.groups?.includes(groupName);
  }

  // Ajusta estos nombres si tus grupos se llaman distinto
  isAdmin(): boolean {
    const me = this.getMeCached();
    return !!me?.is_superuser || !!me?.is_staff || this.hasGroup('ADMIN');
  }

  isAnalista(): boolean {
    return this.isAdmin() || this.hasGroup('ANALISTA');
  }

  isViewer(): boolean {
    return this.isAnalista() || this.hasGroup('VIEWER');
  }

  logout(): void {
    localStorage.removeItem(this.ACCESS_KEY);
    localStorage.removeItem(this.REFRESH_KEY);
    localStorage.removeItem(this.ME_KEY);
    this.loggedIn$.next(false);
  }
}