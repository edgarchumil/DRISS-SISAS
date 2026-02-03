export interface Medication {
  id: number;
  category: string;
  code: string;
  material_name: string;
  monthly_demand_avg: number;
  physical_stock: number;
  months_of_supply: number;
  created_at: string;
  updated_at: string;
}

export interface UserAccount {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  municipality?: string;
  is_active: boolean;
  roles: string[];
  password?: string;
}

export interface Municipality {
  id: number;
  name: string;
}

export interface MunicipalityStock {
  municipality_id: number;
  municipality_name: string;
  total_stock: number;
}

export interface MunicipalityStockItem {
  id: number;
  municipality: number;
  municipality_name: string;
  medication: number;
  medication_name: string;
  stock: number;
  updated_at: string;
}

export interface Movement {
  id: number;
  type: 'ingreso' | 'egreso';
  medication: number;
  medication_name: string;
  municipality?: number | null;
  municipality_name?: string | null;
  user_name?: string | null;
  quantity: number;
  notes: string;
  created_at: string;
}
