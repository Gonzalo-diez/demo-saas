export type AccountMovementType =
  | "invoice"
  | "invoice_reversal"
  | "payment"
  | "credit_note"
  | "adjustment";

export type AccountReferenceType =
  | "sales_invoice"
  | "purchase_invoice"
  | "payment"
  | "manual_adjustment";

export type PaymentMethod =
  | "efectivo"
  | "debito"
  | "credito"
  | "cheque"
  | "otro";

export type InvoiceReferenceSummary = {
  id: number;
  invoice_number: string;
  invoice_date: string;
  total_amount: string | null;
  payment_status: string;
};

export type PaymentAllocationSummary = {
  invoice_id: number;
  invoice_number: string | null;
  amount_applied: string;
};

export type AccountMovementCreator = {
  id: number;
  name: string;
  email: string;
};

// --- Listado general (clientes + proveedores) ---

export type AccountMovementEntityType = "client" | "supplier";

export type AccountMovementSelectedEntity = {
  id: number;
  name: string;
  current_balance: string;
};

// --- Cliente ---

export type ClientAccountMovementClient = {
  id: number;
  name: string;
};

export type ClientAccountMovement = {
  id: number;
  client_id: number;
  movement_type: AccountMovementType;
  amount: string;
  balance_before: string;
  balance_after: string;
  reference_type: AccountReferenceType | null;
  reference_id: number | null;
  payment_method: PaymentMethod | null;
  notes: string | null;
  created_by: number | null;
  created_at: string;
  client?: ClientAccountMovementClient | null;
  creator?: AccountMovementCreator | null;
  reference_summary?: InvoiceReferenceSummary | null;
  allocations: PaymentAllocationSummary[];
};

export type ClientAccountMovementsResponse = {
  items: ClientAccountMovement[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
};

export type ClientAccountMovementsQueryParams = {
  page?: number;
  page_size?: number;
  client_id?: number | null;
  movement_type?: AccountMovementType | "all";
  reference_type?: AccountReferenceType | "all";
};

export type PaymentAllocationInput = {
  invoice_id: number;
  amount: number;
};

export type RegisterClientPaymentInput = {
  amount: number;
  payment_method: PaymentMethod;
  notes?: string | null;
  allocations?: PaymentAllocationInput[];
};

// --- Proveedor ---

export type SupplierAccountMovementSupplier = {
  id: number;
  name: string;
};

export type SupplierAccountMovement = {
  id: number;
  supplier_id: number;
  movement_type: AccountMovementType;
  amount: string;
  balance_before: string;
  balance_after: string;
  reference_type: AccountReferenceType | null;
  reference_id: number | null;
  payment_method: PaymentMethod | null;
  notes: string | null;
  created_by: number | null;
  created_at: string;
  supplier?: SupplierAccountMovementSupplier | null;
  creator?: AccountMovementCreator | null;
  reference_summary?: InvoiceReferenceSummary | null;
  allocations: PaymentAllocationSummary[];
};

export type SupplierAccountMovementsResponse = {
  items: SupplierAccountMovement[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
};

export type SupplierAccountMovementsQueryParams = {
  page?: number;
  page_size?: number;
  supplier_id?: number | null;
  movement_type?: AccountMovementType | "all";
  reference_type?: AccountReferenceType | "all";
};

export type RegisterSupplierPaymentInput = {
  amount: number;
  payment_method: PaymentMethod;
  notes?: string | null;
  allocations?: PaymentAllocationInput[];
};

// --- Pagos de remitos ONLINE (sin cuenta corriente) ---

export type SalesInvoicePayment = {
  id: number;
  sales_invoice_id: number;
  amount: string;
  payment_method: PaymentMethod;
  notes: string | null;
  created_by: number | null;
  created_at: string;
};

export type SalesInvoicePaymentsResponse = {
  payments: SalesInvoicePayment[];
  payment_status: string;
  paid_amount: string;
  total_amount: string | null;
};

export type RegisterSalesInvoicePaymentInput = {
  amount: number;
  payment_method: PaymentMethod;
  notes?: string | null;
};

// --- Métricas de cuenta corriente ---

export type AccountBalanceSummary = {
  total_debt: string;
  total_favor: string;
  net_balance: string;
  debtor_count: number;
  favor_count: number;
};

export type AccountAgingBucket = {
  label: string;
  min_days: number;
  max_days: number | null;
  amount: string;
  invoice_count: number;
};

export type AccountAgingSummary = {
  buckets: AccountAgingBucket[];
  total_pending: string;
};

export type AccountRankingItem = {
  id: number;
  name: string;
  balance: string;
};

export type AccountRankingOrder = "debtors" | "favor";

export type AccountBalanceHistoryPoint = {
  date: string;
  balance: string;
  movement_type: AccountMovementType;
  amount: string;
};