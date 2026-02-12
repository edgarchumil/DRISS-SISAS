import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { BehaviorSubject, finalize, map, tap, throwError } from 'rxjs';

import { AUTH_BASE_URL } from './api.config';
import { LoadingService } from './loading.service';

interface TokenResponse {
  access: string;
  refresh: string;
}

interface RefreshResponse {
  access: string;
}

@Injectable({ providedIn: 'root' })
export class AuthService {
  private readonly accessKey = 'access_token';
  private readonly refreshKey = 'refresh_token';
  private readonly activityKey = 'last_activity_at';
  private readonly loggedIn$ = new BehaviorSubject<boolean>(this.hasSession());

  constructor(private http: HttpClient, private loadingService: LoadingService) {}

  login(username: string, password: string) {
    this.loadingService.show();
    return this.http
      .post<TokenResponse>(`${AUTH_BASE_URL}/token/`, { username, password })
      .pipe(
        tap((tokens) => {
          localStorage.setItem(this.accessKey, tokens.access);
          localStorage.setItem(this.refreshKey, tokens.refresh);
          localStorage.setItem(this.activityKey, String(Date.now()));
          this.loggedIn$.next(true);
        }),
        map(() => true),
        finalize(() => this.loadingService.hide())
      );
  }

  logout(options?: { notifyServer?: boolean }) {
    const notifyServer = options?.notifyServer ?? true;
    const refresh = this.getRefreshToken();
    if (notifyServer && refresh && !this.isTokenExpired(refresh)) {
      this.http.post(`${AUTH_BASE_URL}/logout/`, { refresh }).subscribe({
        next: () => undefined,
        error: () => undefined,
      });
    }
    this.clearSession();
  }

  endSession() {
    this.logout({ notifyServer: false });
  }

  isAccessTokenExpired() {
    const token = this.getAccessToken();
    return token ? this.isTokenExpired(token) : true;
  }

  hasValidRefreshToken() {
    const token = this.getRefreshToken();
    return Boolean(token && !this.isTokenExpired(token));
  }

  isTokenExpired(token: string) {
    const payload = this.parseJwtPayload(token);
    const exp = payload?.['exp'];
    if (typeof exp !== 'number') {
      return true;
    }
    return exp * 1000 <= Date.now();
  }

  private parseJwtPayload(token: string): Record<string, unknown> | null {
    try {
      const parts = token.split('.');
      if (parts.length !== 3) {
        return null;
      }
      const base64 = parts[1].replace(/-/g, '+').replace(/_/g, '/');
      const padded = base64.padEnd(base64.length + ((4 - (base64.length % 4)) % 4), '=');
      const json = atob(padded);
      return JSON.parse(json) as Record<string, unknown>;
    } catch {
      return null;
    }
  }

  private clearSession() {
    localStorage.removeItem(this.accessKey);
    localStorage.removeItem(this.refreshKey);
    localStorage.removeItem(this.activityKey);
    this.loggedIn$.next(false);
  }

  isLoggedIn() {
    return this.loggedIn$.asObservable();
  }

  getAccessToken() {
    return localStorage.getItem(this.accessKey);
  }

  getRefreshToken() {
    return localStorage.getItem(this.refreshKey);
  }

  refreshTokens() {
    const refresh = this.getRefreshToken();
    if (!refresh) {
      return throwError(() => new Error('No refresh token available'));
    }
    if (this.isTokenExpired(refresh)) {
      return throwError(() => new Error('Refresh token expired'));
    }
    return this.http.post<RefreshResponse>(`${AUTH_BASE_URL}/token/refresh/`, { refresh }).pipe(
      tap((token) => {
        localStorage.setItem(this.accessKey, token.access);
        this.loggedIn$.next(true);
      })
    );
  }

  hasSession() {
    return Boolean(localStorage.getItem(this.accessKey) || localStorage.getItem(this.refreshKey));
  }

  private hasToken() {
    return Boolean(localStorage.getItem(this.accessKey));
  }
}
