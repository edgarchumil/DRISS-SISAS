import { CommonModule } from '@angular/common';
import { Component, OnInit, inject } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';

import { UserService } from '../core/user.service';
import { MunicipalityService } from '../core/municipality.service';
import { Municipality } from '../shared/models';
import { UserAccount } from '../shared/models';

const ROLE_OPTIONS = [
  'administradores',
  'usuarios',
  'consultores',
];

@Component({
  selector: 'app-user-form',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterLink],
  templateUrl: './user-form.component.html',
  styleUrl: './user-form.component.scss',
})
export class UserFormComponent implements OnInit {
  isEdit = false;
  isSaving = false;
  userId?: number;
  roleOptions = ROLE_OPTIONS;
  municipalities: Municipality[] = [];
  showPassword = false;

  private fb = inject(FormBuilder);
  private userService = inject(UserService);
  private municipalityService = inject(MunicipalityService);
  private router = inject(Router);
  private route = inject(ActivatedRoute);

  form = this.fb.nonNullable.group({
    username: ['', Validators.required],
    email: ['', Validators.email],
    first_name: [''],
    last_name: [''],
    municipality: [''],
    is_active: [true],
    password: [''],
    roles: this.fb.nonNullable.control<string[]>([]),
  });

  ngOnInit() {
    this.loadMunicipalities();
    const idParam = this.route.snapshot.paramMap.get('id');
    if (idParam) {
      this.isEdit = true;
      this.userId = Number(idParam);
      this.form.controls.password.disable({ emitEvent: false });
      this.userService.get(this.userId).subscribe((user) => {
        this.form.patchValue({
          ...user,
          roles: user.roles ?? [],
        });
      });
    }
  }

  loadMunicipalities() {
    this.municipalityService.list().subscribe({
      next: (response) => {
        this.municipalities = response.results;
      },
    });
  }

  toggleRole(role: string) {
    const currentRoles = new Set(this.form.value.roles ?? []);
    if (currentRoles.has(role)) {
      currentRoles.delete(role);
    } else {
      currentRoles.add(role);
    }
    this.form.patchValue({ roles: Array.from(currentRoles) });
  }

  submit() {
    if (this.form.invalid || this.isSaving) {
      return;
    }
    this.isSaving = true;
    const payload: Partial<UserAccount> = { ...this.form.getRawValue() };
    if (!payload.password) {
      delete payload.password;
    }

    const request = this.isEdit && this.userId
      ? this.userService.update(this.userId, payload)
      : this.userService.create(payload);

    request.subscribe({
      next: () => {
        this.isSaving = false;
        this.router.navigate(['/users']);
      },
      error: () => {
        this.isSaving = false;
      },
    });
  }

  togglePasswordVisibility() {
    if (this.isEdit) {
      return;
    }
    this.showPassword = !this.showPassword;
  }
}
