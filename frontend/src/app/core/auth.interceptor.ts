import { HttpErrorResponse, HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { Router } from '@angular/router';
import { catchError, finalize, switchMap, throwError } from 'rxjs';

import { AuthService } from './auth.service';
import { LoadingService } from './loading.service';

export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const authService = inject(AuthService);
  const router = inject(Router);
  const loadingService = inject(LoadingService);
  const token = authService.getAccessToken();
  const isRefreshRequest = req.url.includes('/auth/token/refresh/');
  const isAuthRequest = req.url.includes('/auth/token/');

  if (token && !isRefreshRequest) {
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
        if (!authService.getRefreshToken()) {
          authService.logout();
          router.navigate(['/login']);
          return throwError(() => error);
        }
        return authService.refreshTokens().pipe(
          switchMap((refreshResponse) => {
            const retryReq = authReq.clone({
              setHeaders: { Authorization: `Bearer ${refreshResponse.access}` }
            });
            return next(retryReq);
          }),
          catchError((refreshError) => {
            authService.logout();
            router.navigate(['/login']);
            return throwError(() => refreshError);
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

  if (!isAuthRequest) {
    loadingService.show();
  }
  return next(req).pipe(
    catchError((error: HttpErrorResponse) => {
      if (isRefreshRequest || error.status !== 401) {
        return throwError(() => error);
      }
      if (!authService.getRefreshToken()) {
        authService.logout();
        router.navigate(['/login']);
        return throwError(() => error);
      }
      return authService.refreshTokens().pipe(
        switchMap((refreshResponse) => {
          const retryReq = req.clone({
            setHeaders: { Authorization: `Bearer ${refreshResponse.access}` }
          });
        return next(retryReq);
      }),
      catchError((refreshError) => {
        authService.logout();
        router.navigate(['/login']);
        return throwError(() => refreshError);
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
