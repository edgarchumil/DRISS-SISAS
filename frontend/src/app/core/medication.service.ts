import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';

import { API_BASE_URL } from './api.config';
import { Medication } from '../shared/models';

interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

@Injectable({ providedIn: 'root' })
export class MedicationService {
  private readonly baseUrl = `${API_BASE_URL}/medications`;

  constructor(private http: HttpClient) {}

  list(search?: string) {
    const params = search ? { search } : undefined;
    return this.http.get<PaginatedResponse<Medication>>(this.baseUrl + '/', { params });
  }

  get(id: number) {
    return this.http.get<Medication>(`${this.baseUrl}/${id}/`);
  }

  create(payload: Partial<Medication>) {
    return this.http.post<Medication>(this.baseUrl + '/', payload);
  }

  update(id: number, payload: Partial<Medication>) {
    return this.http.patch<Medication>(`${this.baseUrl}/${id}/`, payload);
  }

  remove(id: number) {
    return this.http.delete(`${this.baseUrl}/${id}/`);
  }
}
