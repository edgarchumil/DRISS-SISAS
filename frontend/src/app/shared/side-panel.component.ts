import { CommonModule } from '@angular/common';
import { Component, OnInit, inject } from '@angular/core';
import { RouterLink } from '@angular/router';

import { AuthService } from '../core/auth.service';
import { UserService } from '../core/user.service';
import { UserAccount } from './models';

@Component({
  selector: 'app-side-panel',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './side-panel.component.html',
  styleUrl: './side-panel.component.scss',
})
export class SidePanelComponent implements OnInit {
  private userService = inject(UserService);
  private authService = inject(AuthService);

  currentUser?: UserAccount;

  ngOnInit() {
    if (!this.authService.hasSession() || !this.authService.getAccessToken()) {
      this.currentUser = undefined;
      return;
    }
    this.userService.me().subscribe({
      next: (user) => {
        this.currentUser = user;
      },
      error: () => {
        this.currentUser = undefined;
      },
    });
  }

  get displayName() {
    if (!this.currentUser) {
      return 'Usuario SISAS';
    }
    const fullName = `${this.currentUser.first_name} ${this.currentUser.last_name}`.trim();
    return fullName || this.currentUser.username || 'Usuario SISAS';
  }

  get initials() {
    if (!this.currentUser) {
      return 'US';
    }
    const parts = this.displayName.split(' ').filter(Boolean);
    const letters = parts.slice(0, 2).map((part) => part[0]);
    return letters.join('').toUpperCase() || 'US';
  }

  get isAdmin() {
    return (this.currentUser?.roles || []).includes('administradores');
  }
}
