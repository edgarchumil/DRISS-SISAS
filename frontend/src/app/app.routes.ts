import { Routes } from '@angular/router';

import { adminGuard } from './core/admin.guard';
import { authGuard } from './core/auth.guard';
import { LoginComponent } from './auth/login.component';
import { DashboardComponent } from './dashboard/dashboard.component';
import { MedicationFormComponent } from './medications/medication-form.component';
import { MedicationListComponent } from './medications/medication-list.component';
import { MovementsComponent } from './movements/movements.component';
import { ReportsComponent } from './reports/reports.component';
import { UserFormComponent } from './users/user-form.component';
import { UserListComponent } from './users/user-list.component';
import { AuditComponent } from './audit/audit.component';
import { BackupComponent } from './backup/backup.component';

export const routes: Routes = [
  { path: '', redirectTo: 'login', pathMatch: 'full' },
  { path: 'login', component: LoginComponent },
  { path: 'dashboard', component: DashboardComponent, canActivate: [authGuard] },
  {
    path: 'medications',
    canActivate: [authGuard],
    children: [
      { path: '', component: MedicationListComponent },
      { path: 'new', component: MedicationFormComponent },
      { path: ':id/edit', component: MedicationFormComponent },
    ],
  },
  {
    path: 'users',
    canActivate: [authGuard, adminGuard],
    children: [
      { path: '', component: UserListComponent },
      { path: 'new', component: UserFormComponent },
      { path: ':id/edit', component: UserFormComponent },
    ],
  },
  { path: 'movements', component: MovementsComponent, canActivate: [authGuard] },
  { path: 'reports', component: ReportsComponent, canActivate: [authGuard, adminGuard] },
  { path: 'audit', component: AuditComponent, canActivate: [authGuard, adminGuard] },
  { path: 'backup', component: BackupComponent, canActivate: [authGuard, adminGuard] },
];
