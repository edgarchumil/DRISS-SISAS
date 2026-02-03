import { environment } from '../../environments/environment';

const base = environment.apiBaseUrl || '';

export const API_BASE_URL = `${base}/api`;
export const AUTH_BASE_URL = `${base}/api/auth`;
