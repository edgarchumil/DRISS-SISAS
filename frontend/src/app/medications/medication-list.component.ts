import { CommonModule } from '@angular/common';
import { Component, OnInit, inject } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router } from '@angular/router';

import { AuthService } from '../core/auth.service';
import { MedicationService } from '../core/medication.service';
import { MunicipalityService } from '../core/municipality.service';
import { StockEventsService } from '../core/stock-events.service';
import { UserService } from '../core/user.service';
import { Medication, Municipality, MunicipalityStockItem } from '../shared/models';

@Component({
  selector: 'app-medication-list',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './medication-list.component.html',
  styleUrl: './medication-list.component.scss',
})
export class MedicationListComponent implements OnInit {
  medications: Medication[] = [];
  paginated: Medication[] = [];
  municipalities: Municipality[] = [];
  isLoading = false;
  showModal = false;
  isEdit = false;
  editingId?: number;
  showConfirm = false;
  pendingDelete?: Medication;
  currentPage = 1;
  pageSize = 10;
  totalPages = 1;
  searchTerm = '';
  selectedMunicipalityId: number | null = null;
  selectedMunicipalityName = '';
  municipalityStock: number | null = null;
  municipalityStockMap = new Map<number, number>();
  isAllMunicipalities = false;
  municipalityError = '';
  stockSaveError = '';
  editingBaseStock = 0;
  isAdmin = false;
  userMunicipality = '';

  private fb = inject(FormBuilder);
  private medicationService = inject(MedicationService);
  private municipalityService = inject(MunicipalityService);
  private stockEvents = inject(StockEventsService);
  private userService = inject(UserService);
  private authService = inject(AuthService);
  private router = inject(Router);

  form = this.fb.nonNullable.group({
    category: ['', Validators.required],
    code: ['', Validators.required],
    material_name: ['', Validators.required],
    physical_stock: [0, [Validators.required, Validators.min(0)]],
    months_of_supply: [0, [Validators.required, Validators.min(0)]],
  });

  ngOnInit() {
    this.loadCurrentUser();
    this.fetch();
    this.loadMunicipalities();
    this.stockEvents.refresh$.subscribe(() => {
      this.fetch();
      if (this.isAllMunicipalities) {
        this.onMunicipalityChange('all');
      } else if (this.selectedMunicipalityId) {
        this.onMunicipalityChange(String(this.selectedMunicipalityId));
      }
    });
  }

  fetch() {
    this.isLoading = true;
    this.medicationService.list(this.searchTerm.trim() || undefined).subscribe({
      next: (response) => {
        this.medications = [...response.results].sort((a, b) =>
          a.material_name.localeCompare(b.material_name, 'es', { sensitivity: 'base' })
        );
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

  loadMunicipalities() {
    this.municipalityService.list().subscribe({
      next: (response) => {
        this.municipalities = response.results;
        this.applyInitialMunicipalitySelection();
      },
    });
  }

  loadCurrentUser() {
    this.userService.me().subscribe({
      next: (user) => {
        this.userMunicipality = (user.municipality || '').trim();
        this.isAdmin = (user.roles || []).includes('administradores');
        this.applyInitialMunicipalitySelection();
      },
    });
  }

  private applyInitialMunicipalitySelection() {
    if (!this.municipalities.length) {
      return;
    }

    if (this.isAdmin) {
      if (!this.isAllMunicipalities || this.selectedMunicipalityId !== null) {
        this.onMunicipalityChange('all');
      }
      return;
    }

    if (this.userMunicipality) {
      const match = this.matchMunicipalityByName(this.userMunicipality);
      if (match) {
        this.onMunicipalityChange(String(match.id));
        return;
      }
    }

    if (!this.selectedMunicipalityId && !this.isAllMunicipalities) {
      this.onMunicipalityChange('');
    }
  }

  private normalizeText(value: string) {
    return value
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '')
      .toLowerCase()
      .trim();
  }

  private matchMunicipalityByName(name: string) {
    const target = this.normalizeText(name);
    return this.municipalities.find((item) => this.normalizeText(item.name) === target);
  }

  onMunicipalityChange(value: string) {
    if (!this.isAdmin && this.userMunicipality) {
      const match = this.matchMunicipalityByName(this.userMunicipality);
      if (match && String(match.id) !== value) {
        value = String(match.id);
      }
    }
    if (!value) {
      this.selectedMunicipalityId = null;
      this.selectedMunicipalityName = '';
      this.municipalityStock = null;
      this.municipalityStockMap = new Map<number, number>();
      this.isAllMunicipalities = false;
      this.municipalityError = '';
      this.stockSaveError = '';
      this.setPhysicalStockDisabled(false);
      return;
    }
    if (value === 'all') {
      if (!this.isAdmin) {
        return;
      }
      this.isAllMunicipalities = true;
      this.selectedMunicipalityId = null;
      this.selectedMunicipalityName = 'DMS Y DRISS Local';
      this.municipalityError = '';
      this.stockSaveError = '';
      this.setPhysicalStockDisabled(true);
      this.municipalityService.getSummary().subscribe({
        next: (items) => {
          const map = new Map<number, number>();
          let total = 0;
          items.forEach((item) => {
            map.set(item.medication_id, item.total_stock);
            total += item.total_stock;
          });
          this.municipalityStockMap = map;
          this.municipalityStock = total;
          this.updatePagination();
        },
        error: () => {
          this.municipalityStockMap = new Map<number, number>();
          this.municipalityStock = null;
        },
      });
      return;
    }
    const municipalityId = Number(value);
    this.selectedMunicipalityId = Number.isNaN(municipalityId) ? null : municipalityId;
    const selected = this.municipalities.find((item) => item.id === municipalityId);
    this.selectedMunicipalityName = selected ? selected.name : '';
    this.isAllMunicipalities = false;
    this.municipalityError = '';
    this.stockSaveError = '';
    this.setPhysicalStockDisabled(false);
    if (!this.selectedMunicipalityId) {
      this.municipalityStock = null;
      return;
    }
    this.municipalityService.getStock(this.selectedMunicipalityId).subscribe({
      next: (response) => {
        this.municipalityStock = response.total_stock;
      },
      error: () => {
        this.municipalityStock = null;
      },
    });

    this.municipalityService.getStocks(this.selectedMunicipalityId).subscribe({
      next: (items: MunicipalityStockItem[]) => {
        const map = new Map<number, number>();
        items.forEach((item) => {
          map.set(item.medication, item.stock);
        });
        this.municipalityStockMap = map;
        this.updatePagination();
      },
      error: () => {
        this.municipalityStockMap = new Map<number, number>();
        this.updatePagination();
      },
    });
  }

  getMunicipalityStock(medicationId: number, fallback: number) {
    if (!this.selectedMunicipalityId && !this.isAllMunicipalities) {
      return fallback;
    }
    return this.municipalityStockMap.get(medicationId) ?? 0;
  }

  getStockClass(value: number) {
    if (value <= 29) {
      return 'stock-low';
    }
    if (value <= 50) {
      return 'stock-yellow';
    }
    if (value <= 100) {
      return 'stock-orange';
    }
    return 'stock-high';
  }

  openModal() {
    this.form.reset({
      category: '',
      code: '',
      material_name: '',
      physical_stock: this.selectedMunicipalityId ? 0 : 0,
      months_of_supply: 0,
    });
    this.isEdit = false;
    this.editingId = undefined;
    this.showModal = true;
    if (this.isAllMunicipalities) {
      this.municipalityError = '';
      this.setPhysicalStockDisabled(true);
    }
  }

  editMedication(medication: Medication) {
    this.editingBaseStock = medication.physical_stock;
    this.setPhysicalStockDisabled(this.isAllMunicipalities);
    const municipalityStock = this.selectedMunicipalityId
      ? this.municipalityStockMap.get(medication.id) ?? 0
      : medication.physical_stock;
    this.form.patchValue({
      category: medication.category,
      code: medication.code,
      material_name: medication.material_name,
      physical_stock: municipalityStock,
      months_of_supply: medication.months_of_supply,
    });
    this.isEdit = true;
    this.editingId = medication.id;
    this.showModal = true;
  }

  closeModal() {
    this.showModal = false;
  }

  submit() {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }
    if (this.isAllMunicipalities) {
      return;
    }
    const payload = this.form.getRawValue();
    const municipalityId = this.selectedMunicipalityId;
    if (!municipalityId) {
      return;
    }
    const municipalityStock = Number(payload.physical_stock ?? 0);
    const medicationPayload: Partial<Medication> = { ...payload };
    if (municipalityId) {
      delete medicationPayload.physical_stock;
      if (this.isEdit) {
        medicationPayload.physical_stock = this.editingBaseStock;
      } else {
        medicationPayload.physical_stock = 0;
      }
    }
    const request = this.isEdit && this.editingId
      ? this.medicationService.update(this.editingId, medicationPayload)
      : this.medicationService.create(medicationPayload);

    request.subscribe({
      next: (medication) => {
        if (municipalityId) {
          const medicationId = this.isEdit && this.editingId ? this.editingId : medication.id;
          if (!medicationId || Number.isNaN(municipalityStock)) {
            this.showModal = false;
            this.fetch();
            return;
          }
          const normalizedStock = Math.max(0, Math.floor(municipalityStock));
          this.municipalityService
            .setStock(municipalityId, medicationId, normalizedStock)
            .subscribe({
              next: () => {
                this.showModal = false;
                this.fetch();
                this.onMunicipalityChange(String(municipalityId));
                this.stockSaveError = '';
              },
              error: (err) => {
                const message = err?.error?.detail || 'No se pudo guardar el stock para el municipio.';
                this.stockSaveError = message;
              },
            });
          return;
        }
        this.showModal = false;
        this.fetch();
      },
    });
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
    this.totalPages = Math.max(1, Math.ceil(this.medications.length / this.pageSize));
    const start = (this.currentPage - 1) * this.pageSize;
    const end = start + this.pageSize;
    this.paginated = this.medications.slice(start, end);
  }

  private setPhysicalStockDisabled(disabled: boolean) {
    const control = this.form.controls.physical_stock;
    if (disabled) {
      control.disable({ emitEvent: false });
    } else {
      control.enable({ emitEvent: false });
    }
  }

  removeMedication(medication: Medication) {
    this.pendingDelete = medication;
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
    this.medicationService.remove(target.id).subscribe(() => this.fetch());
  }

  logout() {
    this.authService.logout();
    this.router.navigate(['/login']);
  }
}
