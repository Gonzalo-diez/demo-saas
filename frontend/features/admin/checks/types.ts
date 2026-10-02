export type CheckDirection = "received" | "issued";

export type CheckStatus = "pendiente" | "depositado" | "acreditado" | "rechazado";

export type Check = {
  id: number;
  direction: CheckDirection;
  check_number: string;
  bank_name: string | null;
  drawer_name: string | null;
  amount: string;
  issue_date: string;
  payment_date: string;
  due_date: string;
  status: CheckStatus;
  client_id: number | null;
  supplier_id: number | null;
  notes: string | null;
  client_account_movement_id: number | null;
  supplier_account_movement_id: number | null;
  deposited_at: string | null;
  resolved_at: string | null;
  created_by: number | null;
  created_at: string;
  updated_at: string;
};

export type PaginatedChecksResponse = {
  checks: Check[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
};

export type CheckPendingSummaryResponse = {
  pending_amount: string;
  pending_count: number;
  checks: Check[];
};

export type DocumentPendingChecksResponse = {
  pending_amount: string;
  checks: Check[];
};

// Los cheques emitidos (a proveedores) solo pueden imputarse a un remito de
// compra puntual (purchase_invoice); el backend no soporta document_type acá.
export type PaymentAllocationItem = {
  invoice_id: number;
  amount: number;
};

// Los cheques recibidos (de clientes) pueden imputarse a un remito o a un
// presupuesto de venta puntual.
export type ClientPaymentAllocationItem = {
  invoice_id: number;
  amount: number;
  document_type?: "sales_invoice" | "sales_quote";
};

export type RegisterReceivedCheckInput = {
  check_number: string;
  bank_name?: string | null;
  drawer_name?: string | null;
  amount: number;
  issue_date: string;
  payment_date: string;
  due_date: string;
  notes?: string | null;
  allocations?: ClientPaymentAllocationItem[] | null;
};

export type RegisterIssuedCheckInput = {
  check_number: string;
  bank_name?: string | null;
  drawer_name?: string | null;
  amount: number;
  issue_date: string;
  payment_date: string;
  due_date: string;
  notes?: string | null;
  allocations?: PaymentAllocationItem[] | null;
};

export type RejectCheckInput = {
  notes?: string | null;
};

export type ChecksQueryParams = {
  page?: number;
  page_size?: number;
  direction?: CheckDirection | "all";
  status?: CheckStatus | "all";
  client_id?: number;
  supplier_id?: number;
  due_before?: string;
};