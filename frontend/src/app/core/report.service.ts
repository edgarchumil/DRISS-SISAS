import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';

import { API_BASE_URL } from './api.config';

export interface MunicipalityMonthlyReport {
  municipality_id: number;
  municipality_name: string;
  year: number;
  month: number;
  total_quantity: number;
  total_ingresos: number;
  total_pedidos: number;
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
}
