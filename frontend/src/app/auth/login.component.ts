import { CommonModule } from '@angular/common';
import { Component, inject } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router } from '@angular/router';

import { AuthService } from '../core/auth.service';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './login.component.html',
  styleUrl: './login.component.scss',
})
export class LoginComponent {
  errorMessage = '';
  isSubmitting = false;

  phrases = [
    '"Ser salubrista es proteger la vida incluso antes de que el riesgo exista"',
    '"La salud publica no siempre se ve, pero siempre se siente"',
    '"Cada accion preventiva es una vida cuidada"',
    '"Salubristas: guardianes silenciosos del bienestar colectivo"',
    '"Donde hay prevencion, hay futuro"',
    '"Agua segura y saneamiento digno son salud para todos"',
    '"Cuidar el agua es cuidar la vida"',
    '"La salud empieza en el entorno"',
    '"Un ambiente sano es la mejor medicina"',
    '"El saneamiento no es un lujo, es un derecho"',
    '"La salud publica se construye con la comunidad, no solo para ella"',
    '"Educar en salud es empoderar a la poblacion"',
    '"Cuando la comunidad se cuida, el futuro florece"',
    '"El cambio empieza con informacion y compromiso"',
    '"Prevencion hoy, bienestar manana"',
    '"Salud para todos, todos los dias"',
    '"Mas prevencion, menos enfermedad"',
    '"Trabajando por comunidades mas sanas"',
    '"La salud es tarea de todos"',
  ];
  currentPhrase = this.pickRandomPhrase();

  private fb = inject(FormBuilder);
  private authService = inject(AuthService);
  private router = inject(Router);

  form = this.fb.nonNullable.group({
    username: ['', Validators.required],
    password: ['', Validators.required],
  });

  submit() {
    if (this.form.invalid || this.isSubmitting) {
      return;
    }
    this.errorMessage = '';
    this.isSubmitting = true;
    const { username, password } = this.form.getRawValue();

    this.authService.login(username ?? '', password ?? '').subscribe({
      next: () => {
        this.isSubmitting = false;
        this.currentPhrase = this.pickRandomPhrase();
        this.router.navigate(['/dashboard']);
      },
      error: () => {
        this.isSubmitting = false;
        this.errorMessage = 'Credenciales invalidas.';
      },
    });
  }

  private pickRandomPhrase() {
    const index = Math.floor(Math.random() * this.phrases.length);
    return this.phrases[index];
  }
}
