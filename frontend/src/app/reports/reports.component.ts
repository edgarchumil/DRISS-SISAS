import { CommonModule } from '@angular/common';
import { Component, OnInit, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';

import { AuthService } from '../core/auth.service';
import { MedicationService } from '../core/medication.service';
import { MunicipalityService } from '../core/municipality.service';
import { ReportService, MunicipalityMonthlyReport } from '../core/report.service';
import { Medication, Municipality } from '../shared/models';

@Component({
  selector: 'app-reports',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './reports.component.html',
  styleUrl: './reports.component.scss',
})
export class ReportsComponent implements OnInit {
  municipalities: Municipality[] = [];
  selectedMunicipalityId: number | 'all' | null = null;
  selectedMonth = this.getCurrentMonth();
  report: MunicipalityMonthlyReport | null = null;
  paginatedItems: MunicipalityMonthlyReport['items'] = [];
  currentPage = 1;
  pageSize = 10;
  totalPages = 1;
  isLoading = false;
  errorMessage = '';
  showScopeModal = false;
  showAllFormatsModal = false;
  medications: Medication[] = [];
  selectedMedicationIds = new Set<number>();
  scopeType: 'all' | 'selected' = 'all';
  scopeError = '';

  private municipalityService = inject(MunicipalityService);
  private medicationService = inject(MedicationService);
  private reportService = inject(ReportService);
  private authService = inject(AuthService);
  private router = inject(Router);

  ngOnInit() {
    this.loadMunicipalities();
    this.loadMedications();
  }

  loadMunicipalities() {
    this.municipalityService.list().subscribe({
      next: (response) => {
        this.municipalities = response.results;
      },
    });
  }

  loadMedications() {
    this.medicationService.list().subscribe({
      next: (response) => {
        this.medications = response.results;
      },
      error: () => {
        this.medications = [];
      },
    });
  }

  fetchReport() {
    if (this.selectedMunicipalityId === 'all') {
      this.report = null;
      this.openScopeModal();
      return;
    }
    if (!this.selectedMunicipalityId) {
      this.errorMessage = 'Selecciona un municipio.';
      return;
    }
    this.errorMessage = '';
    this.isLoading = true;
    this.reportService.getMunicipalityMonthly(this.selectedMunicipalityId, this.selectedMonth).subscribe({
      next: (report) => {
        this.report = report;
        this.currentPage = 1;
        this.updatePagination();
        this.isLoading = false;
      },
      error: () => {
        this.report = null;
        this.paginatedItems = [];
        this.totalPages = 1;
        this.isLoading = false;
        this.errorMessage = 'No se pudo cargar el reporte.';
      },
    });
  }

  downloadReport() {
    if (this.selectedMunicipalityId === 'all') {
      this.openScopeModal();
      return;
    }
    if (!this.selectedMunicipalityId) {
      this.errorMessage = 'Selecciona un municipio.';
      return;
    }
    this.errorMessage = '';
    this.reportService.downloadMunicipalityMonthly(this.selectedMunicipalityId, this.selectedMonth).subscribe({
      next: (blob) => {
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `reporte_mensual_${this.selectedMonth}.pdf`;
        link.click();
        window.URL.revokeObjectURL(url);
      },
      error: () => {
        this.errorMessage = 'No se pudo descargar el reporte.';
      },
    });
  }

  closeAllFormatsModal() {
    this.showAllFormatsModal = false;
  }

  openScopeModal() {
    this.scopeType = 'all';
    this.scopeError = '';
    this.selectedMedicationIds.clear();
    this.showScopeModal = true;
  }

  closeScopeModal() {
    this.showScopeModal = false;
    this.scopeError = '';
  }

  continueToFormat() {
    if (this.scopeType === 'selected' && this.selectedMedicationIds.size === 0) {
      this.scopeError = 'Selecciona al menos un insumo.';
      return;
    }
    this.scopeError = '';
    this.showScopeModal = false;
    this.showAllFormatsModal = true;
  }

  toggleMedicationSelection(medicationId: number) {
    if (this.selectedMedicationIds.has(medicationId)) {
      this.selectedMedicationIds.delete(medicationId);
    } else {
      this.selectedMedicationIds.add(medicationId);
    }
    this.scopeError = '';
  }

  downloadAllMunicipalities(format: 'pdf' | 'excel') {
    this.errorMessage = '';
    const medicationIds =
      this.scopeType === 'selected' ? Array.from(this.selectedMedicationIds) : undefined;
    this.reportService.downloadAllMunicipalitiesMonthly(this.selectedMonth, format, medicationIds).subscribe({
      next: (blob) => {
        const ext = format === 'pdf' ? 'pdf' : 'xlsx';
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `reporte_todos_municipios_${this.selectedMonth}.${ext}`;
        link.click();
        window.URL.revokeObjectURL(url);
        this.showAllFormatsModal = false;
      },
      error: () => {
        this.errorMessage = 'No se pudo descargar el reporte consolidado.';
      },
    });
  }

  private getCurrentMonth() {
    const now = new Date();
    const month = String(now.getMonth() + 1).padStart(2, '0');
    return `${now.getFullYear()}-${month}`;
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
    const items = this.report?.items ?? [];
    this.totalPages = Math.max(1, Math.ceil(items.length / this.pageSize));
    const start = (this.currentPage - 1) * this.pageSize;
    const end = start + this.pageSize;
    this.paginatedItems = items.slice(start, end);
  }

  logout() {
    this.authService.logout();
    this.router.navigate(['/login']);
  }
}
