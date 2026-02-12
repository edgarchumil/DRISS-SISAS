import { HttpErrorResponse, HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { Router } from '@angular/router';
import { EMPTY, catchError, finalize, switchMap, throwError } from 'rxjs';

import { AuthService } from './auth.service';
import { LoadingService } from './loading.service';

export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const authService = inject(AuthService);
  const router = inject(Router);
  const loadingService = inject(LoadingService);
  const token = authService.getAccessToken();
  const isRefreshRequest = req.url.includes('/auth/token/refresh/');
  const isAuthRequest = req.url.includes('/auth/token/');
  const isLogoutRequest = req.url.includes('/auth/logout/');
  const isApiRequest = req.url.includes('/api/');

  const goToLogin = () => {
    authService.endSession();
    if (!router.url.startsWith('/login')) {
      router.navigate(['/login']);
    }
  };

  if (token && !isRefreshRequest) {
    if (authService.isAccessTokenExpired()) {
      if (!authService.hasValidRefreshToken()) {
        goToLogin();
        return EMPTY;
      }

      if (!isAuthRequest) {
        loadingService.show();
      }

      return authService.refreshTokens().pipe(
        switchMap((refreshResponse) => {
          const retryReq = req.clone({
            setHeaders: { Authorization: `Bearer ${refreshResponse.access}` }
          });
          return next(retryReq);
        }),
        catchError(() => {
          goToLogin();
          return EMPTY;
        }),
        finalize(() => {
          if (!isAuthRequest) {
            loadingService.hide();
          }
        })
      );
    }

    const authReq = req.clone({
      setHeaders: { Authorization: `Bearer ${token}` }
    });
    if (!isAuthRequest) {
      loadingService.show();
    }
    return next(authReq).pipe(
      catchError((error: HttpErrorResponse) => {
        if (error.status !== 401) {
          return throwError(() => error);
        }

        if (isLogoutRequest) {
          return EMPTY;
        }

        if (!authService.hasValidRefreshToken()) {
          goToLogin();
          return EMPTY;
        }

        return authService.refreshTokens().pipe(
          switchMap((refreshResponse) => {
            const retryReq = authReq.clone({
              setHeaders: { Authorization: `Bearer ${refreshResponse.access}` }
            });
            return next(retryReq);
          }),
          catchError(() => {
            goToLogin();
            return EMPTY;
          })
        );
      }),
      finalize(() => {
        if (!isAuthRequest) {
          loadingService.hide();
        }
      })
    );
  }

  if (isApiRequest && !isAuthRequest && !authService.hasValidRefreshToken()) {
    goToLogin();
    return EMPTY;
  }

  if (!isAuthRequest) {
    loadingService.show();
  }
  return next(req).pipe(
    catchError((error: HttpErrorResponse) => {
      if (isRefreshRequest || error.status !== 401) {
        return throwError(() => error);
      }
      if (!authService.hasValidRefreshToken()) {
        goToLogin();
        return EMPTY;
      }
      return authService.refreshTokens().pipe(
        switchMap((refreshResponse) => {
          const retryReq = req.clone({
            setHeaders: { Authorization: `Bearer ${refreshResponse.access}` }
          });
          return next(retryReq);
        }),
        catchError(() => {
          goToLogin();
          return EMPTY;
        })
      );
    }),
    finalize(() => {
      if (!isAuthRequest) {
        loadingService.hide();
      }
    })
  );
};
