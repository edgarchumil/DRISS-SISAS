import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable, catchError, throwError } from 'rxjs';

import { API_BASE_URL } from './api.config';

export interface MunicipalityMonthlyReport {
  municipality_id: number;
  municipality_name: string;
  year: number;
  month: number;
  total_quantity: number;
  total_ingresos: number;
  total_egresos: number;
  items: Array<{
    code: string;
    category: string;
    material_name: string;
    quantity: number;
    type: 'ingreso' | 'egreso';
    user: string;
  }>;
}

@Injectable({ providedIn: 'root' })
export class ReportService {
  private readonly baseUrl = `${API_BASE_URL}/reports/municipality-monthly/`;

  constructor(private http: HttpClient) {}

  getMunicipalityMonthly(municipalityId: number, month: string) {
    return this.http.get<MunicipalityMonthlyReport>(this.baseUrl, {
      params: { municipality_id: municipalityId, month },
    });
  }

  downloadMunicipalityMonthly(municipalityId: number, month: string) {
    return this.http.get(`${this.baseUrl}download/`, {
      params: { municipality_id: municipalityId, month },
      responseType: 'blob',
    });
  }

  downloadAllMunicipalitiesMonthly(month: string, format: 'pdf' | 'excel'): Observable<Blob> {
    const candidates: Array<() => Observable<Blob>> = [
      () =>
        this.http.get(`${this.baseUrl}consolidated/download/`, {
          params: { month, export_format: format },
          responseType: 'blob',
        }),
      () =>
        this.http.get(`${this.baseUrl}all/download/`, {
          params: { month, export_format: format },
          responseType: 'blob',
        }),
      () =>
        this.http.get(`${this.baseUrl}download/`, {
          params: { municipality_id: 'all', month, export_format: format },
          responseType: 'blob',
        }),
      () =>
        this.http.get(`${this.baseUrl}all/`, {
          params: { month, export_format: format },
          responseType: 'blob',
        }),
    ];

    return this.tryCandidates(candidates, 0);
  }

  private tryCandidates(candidates: Array<() => Observable<Blob>>, index: number): Observable<Blob> {
    if (index >= candidates.length) {
      return throwError(() => new Error('No se encontro un endpoint valido para el reporte consolidado.'));
    }

    return candidates[index]().pipe(
      catchError(() => this.tryCandidates(candidates, index + 1))
    );
  }
}
