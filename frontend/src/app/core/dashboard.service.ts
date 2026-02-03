import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';

import { API_BASE_URL } from './api.config';

export interface DashboardStats {
  consumption_monthly: number;
  monthly_ingreso: number;
  monthly_pedido: number;
  materials_total: number;
  users_total: number;
  users_active: number;
  service_rating: number;
}

export interface MonthlyMovement {
  month: string;
  ingreso: number;
  egreso: number;
}

export interface MunicipalitySeries {
  municipality: string;
  total: number;
}

export interface DashboardCharts {
  monthly: MonthlyMovement[];
  distribution: MunicipalitySeries[];
  trend: MunicipalitySeries[];
}

@Injectable({ providedIn: 'root' })
export class DashboardService {
  private readonly baseUrl = `${API_BASE_URL}/dashboard/stats/`;
  private readonly chartsUrl = `${API_BASE_URL}/dashboard/charts/`;

  constructor(private http: HttpClient) {}

  getStats() {
    return this.http.get<DashboardStats>(this.baseUrl);
  }

  getCharts() {
    return this.http.get<DashboardCharts>(this.chartsUrl);
  }
}
