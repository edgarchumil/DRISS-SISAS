import { CommonModule } from '@angular/common';
import { Component, OnInit, inject } from '@angular/core';
import { AbstractControl, FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router } from '@angular/router';

import { AuthService } from '../core/auth.service';
import { UserService } from '../core/user.service';
import { MunicipalityService } from '../core/municipality.service';
import { Municipality } from '../shared/models';
import { UserAccount } from '../shared/models';

@Component({
  selector: 'app-user-list',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './user-list.component.html',
  styleUrl: './user-list.component.scss',
})
export class UserListComponent implements OnInit {
  users: UserAccount[] = [];
  paginated: UserAccount[] = [];
  isLoading = false;
  showModal = false;
  isEdit = false;
  editingId?: number;
  showConfirm = false;
  pendingDelete?: UserAccount;
  searchTerm = '';
  currentPage = 1;
  pageSize = 10;
  totalPages = 1;
  roleOptions = [
    { value: 'administradores', label: 'Administrador' },
    { value: 'usuarios', label: 'Usuario' },
  ];
  municipalities: Municipality[] = [];

  private fb = inject(FormBuilder);
  private userService = inject(UserService);
  private municipalityService = inject(MunicipalityService);
  private authService = inject(AuthService);
  private router = inject(Router);

  form = this.fb.nonNullable.group({
    username: ['', Validators.required],
    email: ['', [Validators.required, Validators.email]],
    first_name: ['', Validators.required],
    last_name: ['', Validators.required],
    municipality: [''],
    password: [''],
    roles: this.fb.nonNullable.control<string[]>([], {
      validators: [this.requireOneRole],
    }),
  });

  ngOnInit() {
    this.fetch();
    this.loadMunicipalities();
  }

  loadMunicipalities() {
    this.municipalityService.list().subscribe({
      next: (response) => {
        this.municipalities = response.results;
      },
    });
  }

  fetch() {
    this.isLoading = true;
    this.userService.list(this.searchTerm.trim() || undefined).subscribe({
      next: (response) => {
        this.users = response.results;
        this.currentPage = 1;
        this.updatePagination();
        this.isLoading = false;
      },
      error: () => {
        this.isLoading = false;
      },
    });
  }

  onSearch(value: string) {
    this.searchTerm = value;
    this.fetch();
  }

  openModal() {
    this.form.reset({
      username: '',
      email: '',
      first_name: '',
      last_name: '',
      municipality: '',
      password: '',
      roles: [],
    });
    this.setPasswordRequired(true);
    this.setPasswordDisabled(false);
    this.isEdit = false;
    this.editingId = undefined;
    this.showModal = true;
  }

  editUser(user: UserAccount) {
    this.form.patchValue({
      username: user.username,
      email: user.email,
      first_name: user.first_name,
      last_name: user.last_name,
      municipality: user.municipality ?? '',
      password: '',
      roles: user.roles ?? [],
    });
    this.setPasswordRequired(false);
    this.setPasswordDisabled(true);
    this.isEdit = true;
    this.editingId = user.id;
    this.showModal = true;
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

  closeModal() {
    this.showModal = false;
  }

  submit() {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }
    const payload = { ...this.form.getRawValue(), is_active: true } as Partial<UserAccount>;
    if (!payload.password) {
      delete payload.password;
    }
    const request = this.isEdit && this.editingId
      ? this.userService.update(this.editingId, payload)
      : this.userService.create(payload);

    request.subscribe(() => {
      this.showModal = false;
      this.fetch();
    });
  }

  removeUser(user: UserAccount) {
    this.pendingDelete = user;
    this.showConfirm = true;
  }

  cancelDelete() {
    this.showConfirm = false;
    this.pendingDelete = undefined;
  }

  confirmDelete() {
    if (!this.pendingDelete) {
      return;
    }
    const target = this.pendingDelete;
    this.showConfirm = false;
    this.pendingDelete = undefined;
    this.userService.remove(target.id).subscribe(() => this.fetch());
  }

  changePage(delta: number) {
    const nextPage = this.currentPage + delta;
    if (nextPage < 1 || nextPage > this.totalPages) {
      return;
    }
    this.currentPage = nextPage;
    this.updatePagination();
  }

  private updatePagination() {
    this.totalPages = Math.max(1, Math.ceil(this.users.length / this.pageSize));
    const start = (this.currentPage - 1) * this.pageSize;
    const end = start + this.pageSize;
    this.paginated = this.users.slice(start, end);
  }

  formatRoles(roles: string[] | undefined) {
    if (!roles || roles.length === 0) {
      return '-';
    }
    return roles
      .map((role) => (role === 'administradores' ? 'Administrador' : 'Usuario'))
      .join(' o ');
  }

  private requireOneRole(control: AbstractControl) {
    const value = control.value as string[] | undefined;
    return value && value.length > 0 ? null : { required: true };
  }

  private setPasswordRequired(isRequired: boolean) {
    const control = this.form.controls.password;
    control.clearValidators();
    if (isRequired) {
      control.addValidators([Validators.required]);
    }
    control.updateValueAndValidity();
  }

  private setPasswordDisabled(disabled: boolean) {
    const control = this.form.controls.password;
    if (disabled) {
      control.disable({ emitEvent: false });
    } else {
      control.enable({ emitEvent: false });
    }
  }

  logout() {
    this.authService.logout();
    this.router.navigate(['/login']);
  }
}
