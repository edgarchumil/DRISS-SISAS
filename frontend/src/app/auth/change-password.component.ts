import { CommonModule } from '@angular/common';
import { Component, inject } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router } from '@angular/router';

import { AuthService } from '../core/auth.service';

@Component({
  selector: 'app-change-password',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './change-password.component.html',
  styleUrl: './change-password.component.scss',
})
export class ChangePasswordComponent {
  private fb = inject(FormBuilder);
  private authService = inject(AuthService);
  private router = inject(Router);

  errorMessage = '';
  isSubmitting = false;
  showCurrentPassword = false;
  showNewPassword = false;
  showConfirmPassword = false;

  form = this.fb.nonNullable.group({
    current_password: ['', Validators.required],
    new_password: ['', [Validators.required, Validators.minLength(8)]],
    confirm_password: ['', Validators.required],
  });

  submit() {
    if (this.form.invalid || this.isSubmitting) {
      this.form.markAllAsTouched();
      if (this.form.controls.current_password.errors?.['required']) {
        this.errorMessage = 'Debes ingresar la contraseña actual.';
      } else if (this.form.controls.new_password.errors?.['required']) {
        this.errorMessage = 'Debes ingresar una nueva contraseña.';
      } else if (this.form.controls.new_password.errors?.['minlength']) {
        this.errorMessage = 'La nueva contraseña debe tener al menos 8 caracteres.';
      } else if (this.form.controls.confirm_password.errors?.['required']) {
        this.errorMessage = 'Debes confirmar la nueva contraseña.';
      }
      return;
    }

    const { current_password, new_password, confirm_password } = this.form.getRawValue();
    if (new_password !== confirm_password) {
      this.errorMessage = 'La confirmacion de la contrasena no coincide.';
      return;
    }

    this.errorMessage = '';
    this.isSubmitting = true;
    this.authService.changePassword(current_password, new_password).subscribe({
      next: () => {
        this.authService.clearPasswordChangeRequired();
        this.router.navigate(['/dashboard']);
      },
      error: (error) => {
        const detail = error?.error?.detail;
        this.errorMessage = typeof detail === 'string' ? detail : 'No se pudo cambiar la contrasena.';
        this.isSubmitting = false;
      },
      complete: () => {
        this.isSubmitting = false;
      },
    });
  }

  logout() {
    this.authService.logout();
    this.router.navigate(['/login']);
  }
}
