import { CommonModule } from '@angular/common';
import { Component, OnInit, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';

import { AuthService } from '../core/auth.service';
import { MunicipalityService } from '../core/municipality.service';
import { ReportService, MunicipalityMonthlyReport } from '../core/report.service';
import { Municipality } from '../shared/models';

@Component({
  selector: 'app-reports',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './reports.component.html',
  styleUrl: './reports.component.scss',
})
export class ReportsComponent implements OnInit {
  municipalities: Municipality[] = [];
  selectedMunicipalityId: number | null = null;
  selectedMonth = this.getCurrentMonth();
  report: MunicipalityMonthlyReport | null = null;
  isLoading = false;
  errorMessage = '';

  private municipalityService = inject(MunicipalityService);
  private reportService = inject(ReportService);
  private authService = inject(AuthService);
  private router = inject(Router);

  ngOnInit() {
    this.loadMunicipalities();
  }

  loadMunicipalities() {
    this.municipalityService.list().subscribe({
      next: (response) => {
        this.municipalities = response.results;
      },
    });
  }

  fetchReport() {
    if (!this.selectedMunicipalityId) {
      this.errorMessage = 'Selecciona un municipio.';
      return;
    }
    this.errorMessage = '';
    this.isLoading = true;
    this.reportService.getMunicipalityMonthly(this.selectedMunicipalityId, this.selectedMonth).subscribe({
      next: (report) => {
        this.report = report;
        this.isLoading = false;
      },
      error: () => {
        this.report = null;
        this.isLoading = false;
        this.errorMessage = 'No se pudo cargar el reporte.';
      },
    });
  }

  downloadReport() {
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

  private getCurrentMonth() {
    const now = new Date();
    const month = String(now.getMonth() + 1).padStart(2, '0');
    return `${now.getFullYear()}-${month}`;
  }

  logout() {
    this.authService.logout();
    this.router.navigate(['/login']);
  }
}
