import { Injectable } from '@angular/core';
import { BehaviorSubject } from 'rxjs';

@Injectable({ providedIn: 'root' })
export class LoadingService {
  private readonly counter$ = new BehaviorSubject<number>(0);
  readonly isLoading$ = this.counter$.asObservable();
  private readonly delayMs = 700;

  show() {
    this.counter$.next(this.counter$.value + 1);
  }

  hide() {
    window.setTimeout(() => {
      this.counter$.next(Math.max(0, this.counter$.value - 1));
    }, this.delayMs);
  }

  reset() {
    this.counter$.next(0);
  }
}
