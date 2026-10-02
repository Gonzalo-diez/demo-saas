export type LedgerPaymentEntry = {
  id: number;
  method: string;
  amount: string;
  date: string;
};

export type LedgerPaymentCreateInput = {
  amount: number;
  method: string;
  date?: string | null;
  notes?: string | null;
};

export type LedgerPaymentUpdateInput = {
  amount?: number | null;
  method?: string | null;
  date?: string | null;
  notes?: string | null;
};

export type LedgerProductLine = {
  product_id: number | null;
  product_name: string;
  quantity: number;
  stock_current: number | null;
};

export type SalesRepSummary = {
  id: number;
  name: string;
};

// --------------- Proveedores ---------------

export type SupplierPurchaseRow = {
  id: number;
  document_type: "purchase_invoice" | "purchase_quote";
  document_number: string;
  purchase_date: string;
  supplier_id: number | null;
  supplier_name: string;
  products: LedgerProductLine[];
  total_quantity: number;
  total_amount: string | null;
  payments: LedgerPaymentEntry[];
  paid_amount: string;
  balance: string;
  payment_status: string;
};

export type SupplierPurchasesGroup = {
  sales_rep: SalesRepSummary | null;
  rows: SupplierPurchaseRow[];
  total: number;
};

export type SupplierPurchasesLedgerResponse = {
  groups: SupplierPurchasesGroup[];
};

export type SupplierPurchasesLedgerQueryParams = {
  sales_rep_id?: number | null;
  date_from?: string | null;
  date_to?: string | null;
};

// --------------- Clientes ---------------

export type ClientSaleRow = {
  id: number;
  document_type: "sales_invoice" | "sales_quote";
  document_number: string;
  sale_date: string;
  client_id: number | null;
  client_name: string;
  sales_type?: "B2B" | "ONLINE" | string | null; // <--- Hacemos opcional con '?'
  products: LedgerProductLine[];
  total_quantity: number;
  total_amount: string | null;
  payments: LedgerPaymentEntry[];
  paid_amount: string;
  balance: string;
  payment_status: string;
};

export type ClientSalesLedgerResponse = {
  items: ClientSaleRow[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
};

export type ClientSalesLedgerQueryParams = {
  page?: number;
  page_size?: number;
  client_id?: number | null;
  sales_rep_id?: number | null;
  unassigned?: boolean;
  date_from?: string | null;
  date_to?: string | null;
};

export type ClientSalesSummaryGroup = {
  sales_rep: SalesRepSummary | null;
  total: number;
};

export type ClientSalesSummaryResponse = {
  groups: ClientSalesSummaryGroup[];
  total_all: number;
};

export type AccountLedgerTab = "suppliers" | "clients";

// --------------- Import Excel ---------------

export type SupplierImportRow = {
  row_number: number;
  product_name: string;
  quantity: number;
  unit_cost: string;
  // Columna "document" del Excel; si la celda está vacía, el backend usa remito.
  document_type: "purchase_invoice" | "purchase_quote";
};

export type SupplierImportRowError = {
  row_number: number;
  errors: string[];
};

export type SupplierImportResult = {
  dry_run: boolean;
  sheet_name: string;
  total_rows_read: number;
  rows_to_import: SupplierImportRow[];
  rows_with_errors: SupplierImportRowError[];
  total_amount: string;
  document_type: "purchase_invoice" | "purchase_quote";
  purchase_invoice_id: number | null;
  purchase_quote_id: number | null;
};

export type ClientImportRow = {
  row_number: number;
  client_name: string;
  matched_client_id: number | null;
  product_name: string;
  quantity: number;
  sale_date: string;
  amount: string;
  payment_method_raw: string | null;
  is_paid: boolean;
  sales_rep_id: number | null;
  sales_rep_name: string | null;
  document_type: "sales_invoice" | "sales_quote";
};

export type ClientImportRowError = {
  row_number: number;
  errors: string[];
};

export type ClientImportPaymentResult = {
  row_number: number;
  client_name: string;
  amount: string;
  allocated_amount: string;
  unassigned_amount: string;
  invoice_numbers: string[];
};

export type ClientImportResult = {
  dry_run: boolean;
  sheet_name: string;
  total_rows_read: number;
  rows_to_import: ClientImportRow[];
  rows_with_errors: ClientImportRowError[];
  payments_applied: ClientImportPaymentResult[];
  document_type: "sales_invoice" | "sales_quote"
  created_sales_invoice_ids: number[];
  created_sales_quote_ids: number[];
  rows_skipped_already_imported: number;
};