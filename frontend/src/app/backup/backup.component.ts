import { CommonModule } from '@angular/common';
import { Component, inject } from '@angular/core';
import { Router } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { HttpErrorResponse } from '@angular/common/http';

import { AuthService } from '../core/auth.service';
import { BackupService } from '../core/backup.service';

@Component({
  selector: 'app-backup',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './backup.component.html',
  styleUrl: './backup.component.scss',
})
export class BackupComponent {
  isLoading = false;
  errorMessage = '';
  showModal = false;
  password = '';
  showPassword = false;

  private backupService = inject(BackupService);
  private authService = inject(AuthService);
  private router = inject(Router);

  openConfirm() {
    this.errorMessage = '';
    this.password = '';
    this.showPassword = false;
    this.showModal = true;
  }

  closeConfirm() {
    this.showModal = false;
    this.password = '';
    this.showPassword = false;
  }

  downloadBackup() {
    if (!this.password) {
      this.errorMessage = 'Ingresa tu contrasena para continuar.';
      return;
    }
    this.isLoading = true;
    this.errorMessage = '';
    this.backupService.download(this.password).subscribe({
      next: (blob) => {
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `backup_${new Date().toISOString().slice(0, 10)}.zip`;
        link.click();
        window.URL.revokeObjectURL(url);
        this.isLoading = false;
        this.showModal = false;
        this.password = '';
        this.showPassword = false;
      },
      error: (err: HttpErrorResponse) => {
        const fallback = 'Contrasena incorrecta o sin permisos.';
        if (typeof err?.error === 'string' && err.error.trim()) {
          this.errorMessage = err.error;
        } else if (err?.error instanceof Blob) {
          err.error
            .text()
            .then((text) => {
              this.errorMessage = text?.trim() || fallback;
            })
            .catch(() => {
              this.errorMessage = fallback;
            });
        } else {
          this.errorMessage = fallback;
        }
        this.isLoading = false;
      },
    });
  }

  logout() {
    this.authService.logout();
    this.router.navigate(['/login']);
  }

  togglePasswordVisibility() {
    this.showPassword = !this.showPassword;
  }
}
