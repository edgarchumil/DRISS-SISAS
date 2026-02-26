import { CommonModule } from '@angular/common';
import { Component, OnInit, inject } from '@angular/core';
import { FormBuilder, FormControl, FormGroup, ReactiveFormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { catchError, of } from 'rxjs';

import { AuthService } from '../core/auth.service';
import { MedicationService } from '../core/medication.service';
import { MovementService } from '../core/movement.service';
import { MunicipalityService } from '../core/municipality.service';
import { StockEventsService } from '../core/stock-events.service';
import { UserService } from '../core/user.service';
import { Medication, Movement, Municipality } from '../shared/models';

type MovementType = 'ingreso' | 'egreso';

interface MovementItem {
  id: number;
  type: MovementType;
  medication: string;
  quantity: number;
  date: string;
  notes: string;
}

@Component({
  selector: 'app-movements',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './movements.component.html',
  styleUrl: './movements.component.scss',
})
export class MovementsComponent implements OnInit {
  medications: Medication[] = [];
  municipalities: Municipality[] = [];
  movements: MovementItem[] = [];
  paginated: MovementItem[] = [];
  isLoading = false;

  showTypeModal = false;
  showFormModal = false;
  showConfirmModal = false;
  selectedType: MovementType | null = null;
  currentPage = 1;
  pageSize = 10;
  totalPages = 1;

  private fb = inject(FormBuilder);
  private medicationService = inject(MedicationService);
  private movementService = inject(MovementService);
  private municipalityService = inject(MunicipalityService);
  private stockEvents = inject(StockEventsService);
  private userService = inject(UserService);
  private authService = inject(AuthService);
  private router = inject(Router);

  currentMunicipality = '';
  userMunicipalityLocked = false;
  movementError = '';
  lastError = '';
  egresoMunicipalityControl = new FormControl<number | null>(null);

  ingresoForm = this.fb.group({});
  ingresoNotes = new FormControl('', { nonNullable: true });
  egresoForm = this.fb.group({});
  egresoNotes = new FormControl('', { nonNullable: true });

  ngOnInit() {
    this.loadCatalogs();
    this.loadMovements();
    this.loadUserMunicipality();
    this.loadMunicipalities();
  }

  loadCatalogs() {
    this.isLoading = true;
    this.medicationService.list().subscribe({
      next: (response) => {
        this.medications = response.results;
        this.buildIngresoForm();
        this.buildEgresoForm();
        this.isLoading = false;
      },
      error: () => {
        this.isLoading = false;
      },
    });
  }

  loadMovements() {
    this.isLoading = true;
    this.movementService.list().subscribe({
      next: (response) => {
        this.movements = response.results.map((item) => this.mapMovement(item));
        this.currentPage = 1;
        this.updatePagination();
        this.isLoading = false;
      },
      error: () => {
        this.isLoading = false;
      },
    });
  }

  loadUserMunicipality() {
    this.userService.me().subscribe({
      next: (user) => {
        this.currentMunicipality = (user.municipality || '').trim();
        this.syncUserMunicipalitySelection();
      },
      error: () => {
        this.currentMunicipality = '';
        this.syncUserMunicipalitySelection();
      },
    });
  }

  loadMunicipalities() {
    this.municipalityService.list().subscribe({
      next: (response) => {
        this.municipalities = response.results;
        this.syncUserMunicipalitySelection();
      },
      error: () => {
        this.municipalities = [];
        this.syncUserMunicipalitySelection();
      },
    });
  }

  openTypeModal() {
    this.lastError = '';
    this.showTypeModal = true;
  }

  chooseType(type: MovementType) {
    this.selectedType = type;
    if (type === 'egreso') {
      this.syncUserMunicipalitySelection();
    }
    this.showTypeModal = false;
    this.openFormModal();
  }

  openFormModal() {
    this.movementError = '';
    this.showFormModal = true;
  }

  closeFormModal() {
    this.showFormModal = false;
  }

  openConfirmModal() {
    this.showConfirmModal = true;
  }

  closeConfirmModal() {
    this.showConfirmModal = false;
  }

  confirmEgreso() {
    this.showConfirmModal = false;
    this.submit();
  }

  get activeForm() {
    return this.selectedType === 'egreso' ? this.egresoForm : this.ingresoForm;
  }

  submit() {
    if (!this.selectedType) {
      return;
    }
    if (this.selectedType === 'ingreso') {
      this.submitIngreso();
      return;
    }
    if (this.selectedType === 'egreso') {
      this.submitEgreso();
      return;
    }
  }

  private buildIngresoForm() {
    const group: Record<string, FormControl<number>> = {};
    this.medications.forEach((med) => {
      group[String(med.id)] = new FormControl(0, { nonNullable: true });
    });
    this.ingresoForm = new FormGroup(group);
  }

  private buildEgresoForm() {
    const group: Record<string, FormControl<number>> = {};
    this.medications.forEach((med) => {
      group[String(med.id)] = new FormControl(0, { nonNullable: true });
    });
    this.egresoForm = new FormGroup(group);
  }

  private submitIngreso() {
    const quantities = this.ingresoForm.getRawValue() as Record<string, number>;
    const entries = Object.entries(quantities)
      .map(([id, value]) => ({ id: Number(id), quantity: Number(value) }))
      .filter((entry) => entry.quantity && entry.quantity > 0);

    if (entries.length === 0) {
      this.ingresoForm.markAllAsTouched();
      this.movementError = 'Ingresa al menos una cantidad mayor a 0.';
      this.lastError = this.movementError;
      return;
    }

    const notes = this.ingresoNotes.value;
    const payload = entries.map((entry) => ({
      type: 'ingreso' as const,
      medication: entry.id,
      quantity: entry.quantity,
      notes,
    }));

    this.movementService
      .createBulk(payload)
      .pipe(catchError((error) => of({ error } as any)))
      .subscribe((result: any) => {
        if (result?.error) {
          const errorPayload = result?.error?.error ?? result?.error;
          const message =
            errorPayload?.detail ||
            errorPayload?.non_field_errors?.[0] ||
            'No se pudo guardar todos los ingresos.';
          this.movementError = message;
          this.lastError = message;
          return;
        }

        (result as any[]).forEach((movement: any) => {
          this.movements.unshift(this.mapMovement(movement));
        });
        this.updatePagination();
        this.stockEvents.notifyRefresh();
        this.showFormModal = false;
        this.ingresoForm.reset();
        this.ingresoNotes.setValue('');
      });
  }

  private submitEgreso() {
    const municipality = this.egresoMunicipalityControl.value;
    if (!municipality) {
      this.movementError = 'Selecciona el municipio de destino.';
      this.lastError = this.movementError;
      return;
    }

    const values = this.egresoForm.getRawValue() as Record<string, number>;
    const entries: Array<{ medId: number; quantity: number }> = [];

    Object.entries(values).forEach(([medId, qty]) => {
      const quantity = Number(qty);
      if (quantity && quantity > 0) {
        entries.push({ medId: Number(medId), quantity });
      }
    });

    if (entries.length === 0) {
      this.egresoForm.markAllAsTouched();
      this.movementError = 'Ingresa al menos una cantidad mayor a 0.';
      this.lastError = this.movementError;
      return;
    }

    const notes = this.egresoNotes.value;
    const payload = entries.map((entry) => ({
      type: 'egreso' as const,
      medication: entry.medId,
      quantity: entry.quantity,
      notes,
      municipality,
    }));

    this.movementService
      .createBulk(payload)
      .pipe(catchError((error) => of({ error } as any)))
      .subscribe((result: any) => {
        if (result?.error) {
          const errorPayload = result?.error?.error ?? result?.error;
          const message =
            errorPayload?.detail ||
            errorPayload?.non_field_errors?.[0] ||
            'No se pudo guardar todos los egresos.';
          this.movementError = message;
          this.lastError = message;
          return;
        }

        const movementIds = (result as any[])
          .map((movement: any) => Number(movement?.id))
          .filter((id: number) => Number.isFinite(id));
        if (movementIds.length) {
          this.downloadDispatchReport(movementIds);
        }

        (result as any[]).forEach((movement: any) => {
          this.movements.unshift(this.mapMovement(movement));
        });
        this.updatePagination();
        this.stockEvents.notifyRefresh();
        this.showFormModal = false;
        this.egresoForm.reset();
        this.egresoNotes.setValue('');
        this.syncUserMunicipalitySelection();
      });
  }

  private normalizeText(value: string) {
    return value
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '')
      .toLowerCase()
      .trim();
  }

  private canonicalMunicipalityName(value: string) {
    return this.normalizeText(value)
      .replace(/\b(dms|red|driss|local)\b/g, ' ')
      .replace(/\s+/g, ' ')
      .trim();
  }

  private syncUserMunicipalitySelection() {
    if (!this.currentMunicipality || !this.municipalities.length) {
      this.userMunicipalityLocked = false;
      this.egresoMunicipalityControl.enable({ emitEvent: false });
      return;
    }

    const target = this.canonicalMunicipalityName(this.currentMunicipality);
    const match = this.municipalities.find((item) => {
      const candidate = this.canonicalMunicipalityName(item.name);
      if (!target || !candidate) {
        return false;
      }
      return candidate === target || candidate.includes(target) || target.includes(candidate);
    });

    if (match) {
      this.userMunicipalityLocked = true;
      this.egresoMunicipalityControl.setValue(match.id, { emitEvent: false });
      this.egresoMunicipalityControl.disable({ emitEvent: false });
      return;
    }

    this.userMunicipalityLocked = false;
    this.egresoMunicipalityControl.enable({ emitEvent: false });
  }

  private downloadDispatchReport(ids: number[]) {
    this.movementService.dispatchReport(ids).subscribe({
      next: (blob) => {
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = 'despacho_insumos.pdf';
        link.click();
        window.URL.revokeObjectURL(url);
      },
      error: () => {
        // descarga opcional, no bloquear el flujo
      },
    });
  }

  private mapMovement(movement: Movement): MovementItem {
    return {
      id: movement.id,
      type: movement.type,
      medication: movement.medication_name,
      quantity: movement.quantity,
      date: movement.created_at.split('T')[0],
      notes: movement.notes,
    };
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
    this.totalPages = Math.max(1, Math.ceil(this.movements.length / this.pageSize));
    const start = (this.currentPage - 1) * this.pageSize;
    const end = start + this.pageSize;
    this.paginated = this.movements.slice(start, end);
  }

  logout() {
    this.authService.logout();
    this.router.navigate(['/login']);
  }
}
