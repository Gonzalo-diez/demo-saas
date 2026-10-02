export type SalesRep = {
  id: number;
  name: string;
  email: string;
  phone: string | null;
  home_lat: number;
  home_lng: number;
  coverage_radius_km: number;
  home_h3_index: string;
  is_active: boolean;
  is_superuser: boolean;
  created_at: string;
  updated_at: string;
};

export type SalesRepStatusFilter = "" | "active" | "inactive";
export type SalesRepSort = "" | "name" | "created_at";

export type SalesRepsQueryParams = {
  page?: number;
  page_size?: number;
  search?: string;
  status?: SalesRepStatusFilter;
  sort?: SalesRepSort;
};

export type SalesRepsResponse = {
  sales_reps: SalesRep[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
};

export type CreateSalesRepInput = {
  name: string;
  email: string;
  phone?: string | null;
  home_lat?: number;
  home_lng?: number;
  coverage_radius_km?: number;
  home_h3_index?: string;
  password: string;
  is_active: boolean;
  is_superuser: boolean;
};

export type UpdateSalesRepInput = Partial<CreateSalesRepInput>;

export type ImportMode = "upsert" | "create";

export type SalesRepImportRow = {
  name: string;
  email: string;
  phone?: string;
  home_lat: number;
  home_lng: number;
  coverage_radius_km: number;
  is_active: boolean;
  is_superuser: boolean;
  password: string;
}

export type SalesRepImportRowError = {
  row_number: number;
  data: Record<string, unknown>;
  errors: string[];
}

export type SalesRepImportPreviewResponse = {
  total_rows: number;
  valid_rows: number;
  invalid_rows: number;
  rows_valid: SalesRepImportRow[];
  rows_invalid: SalesRepImportRowError[];
}

export type SalesRepImportCommitRequest = {
  rows: SalesRepImportRow[];
  mode: ImportMode;  
}

export type SalesRepImportCommitResponse = {
  total: number;
  created: number;
  updated: number;
  failed: number;
  errors: string[];
}