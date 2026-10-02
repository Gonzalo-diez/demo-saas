export type Supplier = {
  id: number;
  name: string;
  tax_id: string | null;
  email: string | null;
  phone: string | null;
  address: string | null;
  is_active: boolean;
  current_balance: string;
  created_at: string;
  updated_at: string | null;
};

export type SupplierStatusFilter = "" | "active" | "inactive";

export type SupplierListParams = {
  page?: number;
  page_size?: number;
  search?: string;
  status?: SupplierStatusFilter;
};

export type SupplierListResponse = {
  suppliers: Supplier[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
};

export type CreateSupplierInput = {
  name: string;
  tax_id?: string | null;
  email?: string | null;
  phone?: string | null;
  address?: string | null;
  is_active: boolean;
};

export type UpdateSupplierInput = Partial<CreateSupplierInput>;

export type ImportMode = "upsert" | "create";

export type SupplierImportRow = {
  name: string;
  tax_id: string | null;
  email: string | null;
  phone: string | null;
  address: string | null;
};

export type SupplierImportRowError = {
  row_number: number;
  data: Record<string, unknown>;
  errors: string[];
};

export type SupplierImportPreviewItem = {
  row_number: number;
  name: string;
  action: string;
  errors: string[];
};

export type SupplierImportPreviewResponse = {
  total_rows: number;
  valid_rows: number;
  invalid_rows: number;
  rows_valid: SupplierImportRow[];
  rows_invalid: SupplierImportRowError[];
  create_count: number;
  update_count: number;
  skip_count: number;
  items: SupplierImportPreviewItem[];
};

export type SupplierImportCommitRequest = {
  rows: SupplierImportRow[];
  mode: ImportMode;  
}

export type SupplierImportCommitResponse = {
  created: number;
  updated: number;
  skipped: number;
};