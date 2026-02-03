import { CommonModule } from '@angular/common';
import { Component, OnDestroy, OnInit, inject } from '@angular/core';
import { NavigationCancel, NavigationEnd, NavigationError, NavigationStart, Router, RouterOutlet } from '@angular/router';
import {
  asyncScheduler,
  combineLatest,
  distinctUntilChanged,
  filter,
  fromEvent,
  map,
  merge,
  observeOn,
  startWith,
  Subscription,
} from 'rxjs';

import { AuthService } from './core/auth.service';
import { LoadingService } from './core/loading.service';
import { SidePanelComponent } from './shared/side-panel.component';

@Component({
  selector: 'app-root',
  imports: [CommonModule, RouterOutlet, SidePanelComponent],
  templateUrl: './app.component.html',
  styleUrl: './app.component.scss'
})
export class AppComponent implements OnInit, OnDestroy {
  title = 'Control de Medicamentos';

  private authService = inject(AuthService);
  private router = inject(Router);
  private loadingService = inject(LoadingService);
  private idleTimer?: number;
  private activitySub?: Subscription;
  private readonly idleTimeoutMs = 5 * 60 * 1000;
  private readonly lastActivityKey = 'last_activity_at';

  showSidePanel$ = this.router.events.pipe(
    filter(
      (event) =>
        event instanceof NavigationStart ||
        event instanceof NavigationEnd ||
        event instanceof NavigationCancel ||
        event instanceof NavigationError
    ),
    map(() => this.authService.hasSession() && !this.router.url.startsWith('/login')),
    startWith(this.authService.hasSession() && !this.router.url.startsWith('/login')),
    distinctUntilChanged(),
    observeOn(asyncScheduler)
  );

  pageLoading$ = combineLatest([
    this.router.events.pipe(
      filter(
        (event) =>
          event instanceof NavigationStart ||
          event instanceof NavigationEnd ||
          event instanceof NavigationCancel ||
          event instanceof NavigationError
      ),
      map((event) => event instanceof NavigationStart),
      startWith(false)
    ),
    this.loadingService.isLoading$.pipe(map((count) => count > 0), startWith(false)),
  ]).pipe(
    map(([routerLoading, httpLoading]) => routerLoading || httpLoading),
    distinctUntilChanged(),
    observeOn(asyncScheduler)
  );

  showGlobalLogout$ = this.router.events.pipe(
    filter(
      (event) =>
        event instanceof NavigationStart ||
        event instanceof NavigationEnd ||
        event instanceof NavigationCancel ||
        event instanceof NavigationError
    ),
    map(() => {
      const path = this.router.url;
      return (
        this.authService.hasSession() &&
        !path.startsWith('/login') &&
        !path.startsWith('/dashboard') &&
        !path.startsWith('/medications') &&
        !path.startsWith('/movements') &&
        !path.startsWith('/users') &&
        !path.startsWith('/reports') &&
        !path.startsWith('/audit') &&
        !path.startsWith('/backup')
    );
  }),
  startWith(
    this.authService.hasSession() &&
      !this.router.url.startsWith('/login') &&
      !this.router.url.startsWith('/dashboard') &&
      !this.router.url.startsWith('/medications') &&
      !this.router.url.startsWith('/movements') &&
      !this.router.url.startsWith('/users') &&
      !this.router.url.startsWith('/reports') &&
      !this.router.url.startsWith('/audit') &&
      !this.router.url.startsWith('/backup')
  ),
    distinctUntilChanged(),
    observeOn(asyncScheduler)
  );

  ngOnInit() {
    this.router.events.subscribe((event) => {
      if (event instanceof NavigationEnd || event instanceof NavigationCancel || event instanceof NavigationError) {
        this.resetIdleTimer();
      }
    });
    this.setupIdleTracking();
    this.resetIdleTimer();
  }

  ngOnDestroy() {
    if (this.idleTimer) {
      window.clearTimeout(this.idleTimer);
    }
    this.activitySub?.unsubscribe();
  }

  private setupIdleTracking() {
    const activityEvents = merge(
      fromEvent(document, 'mousemove'),
      fromEvent(document, 'keydown'),
      fromEvent(document, 'click'),
      fromEvent(document, 'scroll'),
      fromEvent(document, 'touchstart')
    );
    this.activitySub = activityEvents.subscribe(() => this.resetIdleTimer());
  }

  private resetIdleTimer() {
    if (!this.authService.hasSession()) {
      return;
    }
    const lastActivity = this.getLastActivity();
    if (lastActivity && Date.now() - lastActivity > this.idleTimeoutMs) {
      this.handleIdleTimeout();
      return;
    }
    this.setLastActivity(Date.now());
    if (this.idleTimer) {
      window.clearTimeout(this.idleTimer);
    }
    this.idleTimer = window.setTimeout(() => this.handleIdleTimeout(), this.idleTimeoutMs);
  }

  private handleIdleTimeout() {
    if (!this.authService.hasSession()) {
      return;
    }
    this.authService.logout();
    this.router.navigate(['/login']);
  }

  private getLastActivity() {
    const raw = localStorage.getItem(this.lastActivityKey);
    return raw ? Number(raw) : 0;
  }

  private setLastActivity(timestamp: number) {
    localStorage.setItem(this.lastActivityKey, String(timestamp));
  }

  logout() {
    this.authService.logout();
    this.router.navigate(['/login']);
  }
}
