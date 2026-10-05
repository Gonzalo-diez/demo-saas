export type Action =
  | "create"
  | "update"
  | "skip"
  | "error"

export type ClientBranch = {
  id: number;
  client_id: number;
  name: string;
  address?: string;
  city?: string;
  lat?: number;
  lng?: number;
  h3_index?: string;
  contact_name?: string | null;
  contact_phone?: string | null;
  reference?: string | null;
  is_main: boolean;
  is_active: boolean;
};

export type Client = {
  id: number;
  name: string;
  client_type: string;
  tax_id: string | null;
  email: string | null;
  phone: string | null;
  sales_rep_id: number | null;
  is_active: boolean;
  current_balance: string;
  created_at?: string;
  updated_at?: string;
  branches: ClientBranch[];
};

export type ClientsQueryParams = {
  page?: number;
  page_size?: number;
  search?: string;
  status?: "active" | "inactive" | "";
  sort?: "name" | "created_at" | "";
  sales_rep_id?: number;
};

export type ClientsResponse = {
  clients: Client[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
};

export type CreateClientBranchInput = {
  name: string;
  address?: string | null;
  city?: string | null;
  lat?: number | null;
  lng?: number | null;
  h3_index?: string | null;
  contact_name?: string | null;
  contact_phone?: string | null;
  reference?: string | null;
  is_main: boolean;
  is_active?: boolean;
};

export type UpdateClientBranchInput = Partial<CreateClientBranchInput>;

export type CreateClientInput = {
  name: string;
  tax_id?: string | null;
  email?: string | null;
  phone?: string | null;
  client_type: string;
  is_active: boolean;
  password: string;
  branches: CreateClientBranchInput[];
};

export type UpdateClientInput = {
  name?: string;
  tax_id?: string | null;
  email?: string | null;
  phone?: string | null;
  is_active?: boolean;
  password?: string | null;
};

export type ImportMode = "upsert" | "create" | "update";

export type ClientImportRow = {
  client_name: string;
  email?: string | null;
  password?: string | null;
  tax_id: string;
  client_type: string;
  is_active: boolean;
  branch_name: string;
  address: string;
  city: string;
  lat: number;
  lng: number;
  contact_name: string;
  contact_phone: string;
  reference?: string | null;
  is_main: boolean;
  branch_is_active: boolean;
};

export type ClientImportError = {
  row_number: number;
  data: Record<string, unknown>;
  errors: string[];
}

export type ClientImportPreviewItem = {
  row_number: number;
  client_name: string;
  branch_name: string;
  client_action: Action;
  branch_action: Action;
  errors: string[];
};

export type ClientImportPreviewResponse = {
  total_rows: number;
  clients_to_create: number;
  clients_to_update: number;
  branches_to_create: number;
  branches_to_update: number;
  valid_rows: number;
  invalid_rows: number;
  skipped_rows: number;
  items: ClientImportPreviewItem[];
  rows_valid: ClientImportRow[];
  rows_invalid: ClientImportError[];
};

export type ClientImportCommitRequest = {
  rows: ClientImportRow[];
  mode: ImportMode;
};

export type GeneratedClientPassword = {
  client_name: string;
  email?: string | null;
  password: string;
};

export type ClientImportCommitResponse = {
  clients_created: number;
  clients_updated: number;
  branches_created: number;
  branches_updated: number;
  skipped_rows: number;
  generated_passwords: GeneratedClientPassword[];
};