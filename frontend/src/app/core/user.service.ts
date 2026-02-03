import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';

import { API_BASE_URL } from './api.config';
import { UserAccount } from '../shared/models';

interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

@Injectable({ providedIn: 'root' })
export class UserService {
  private readonly baseUrl = `${API_BASE_URL}/users`;

  constructor(private http: HttpClient) {}

  list(search?: string) {
    const params = search ? { search } : undefined;
    return this.http.get<PaginatedResponse<UserAccount>>(this.baseUrl + '/', { params });
  }

  me() {
    return this.http.get<UserAccount>(`${this.baseUrl}/me/`);
  }

  get(id: number) {
    return this.http.get<UserAccount>(`${this.baseUrl}/${id}/`);
  }

  create(payload: Partial<UserAccount>) {
    return this.http.post<UserAccount>(this.baseUrl + '/', payload);
  }

  update(id: number, payload: Partial<UserAccount>) {
    return this.http.put<UserAccount>(`${this.baseUrl}/${id}/`, payload);
  }

  remove(id: number) {
    return this.http.delete(`${this.baseUrl}/${id}/`);
  }
}
