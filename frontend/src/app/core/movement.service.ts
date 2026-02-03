import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';

import { API_BASE_URL } from './api.config';
import { Movement } from '../shared/models';

interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

interface MovementPayload {
  type: 'ingreso' | 'egreso';
  medication: number;
  quantity: number;
  notes?: string;
  municipality?: number;
}

@Injectable({ providedIn: 'root' })
export class MovementService {
  private readonly baseUrl = `${API_BASE_URL}/movements`;

  constructor(private http: HttpClient) {}

  list() {
    return this.http.get<PaginatedResponse<Movement>>(this.baseUrl + '/');
  }

  create(payload: MovementPayload) {
    return this.http.post<Movement>(this.baseUrl + '/', payload);
  }

  createBulk(items: MovementPayload[]) {
    return this.http.post<Movement[]>(`${this.baseUrl}/bulk/`, { items });
  }

  dispatchReport(ids: number[]) {
    return this.http.post(`${this.baseUrl}/dispatch-report/`, { ids }, { responseType: 'blob' });
  }
}
