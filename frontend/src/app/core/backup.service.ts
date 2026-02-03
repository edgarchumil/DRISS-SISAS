import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';

import { API_BASE_URL } from './api.config';

@Injectable({ providedIn: 'root' })
export class BackupService {
  private readonly baseUrl = `${API_BASE_URL}/backup/download/`;

  constructor(private http: HttpClient) {}

  download(password: string) {
    return this.http.post(this.baseUrl, { password }, { responseType: 'blob' });
  }
}
