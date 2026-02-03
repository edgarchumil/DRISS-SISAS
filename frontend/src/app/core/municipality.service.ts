import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';

import { API_BASE_URL } from './api.config';
import { Municipality, MunicipalityStock, MunicipalityStockItem } from '../shared/models';

interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

@Injectable({ providedIn: 'root' })
export class MunicipalityService {
  private readonly baseUrl = `${API_BASE_URL}/municipalities`;

  constructor(private http: HttpClient) {}

  list() {
    return this.http.get<PaginatedResponse<Municipality>>(this.baseUrl + '/');
  }

  getStock(municipalityId: number) {
    return this.http.get<MunicipalityStock>(`${this.baseUrl}/${municipalityId}/stock/`);
  }

  getStocks(municipalityId: number) {
    return this.http.get<MunicipalityStockItem[]>(`${this.baseUrl}/${municipalityId}/stocks/`);
  }

  setStock(municipalityId: number, medicationId: number, stock: number) {
    return this.http.post<MunicipalityStockItem>(`${API_BASE_URL}/municipality-stocks/`, {
      municipality: Number(municipalityId),
      medication: Number(medicationId),
      stock: Number(stock),
    });
  }

  getSummary() {
    return this.http.get<Array<{ medication_id: number; total_stock: number }>>(
      `${API_BASE_URL}/municipality-stocks/summary/`
    );
  }
}
