export type SalesInvoiceStatus = "draft"| "confirmed" | "cancelled";

export type SalesType = "B2B" | "ONLINE";

export type DialogView = "manual" | "import";

export type SalesInvoiceClient = {
  id: number;
  name: string;
};

export type SalesInvoiceClientBranch = {
  id: number;
  client_id: number;
  name: string;
  address: string | null;
  city: string | null;
};

export type SalesInvoiceSalesRep = {
  id: number;
  name: string;
  email: string;
};

export type SalesInvoiceItem = {
  id: number;
  product_id: number;
  quantity: number;
  unit_cost: string;
  unit_price: string;
  subtotal_cost: string;
  subtotal: string;
  margin_amount: string;
};

export type SalesInvoicePaymentStatus = "pending" | "partial" | "paid";

export type SalesInvoice = {
  id: number;
  order_id: number | null;
  sales_type: SalesType;
  client_id: number | null;
  client_branch_id: number | null;
  sales_rep_id: number;
  customer_name: string | null;
  customer_phone: string | null;
  customer_email: string | null;
  delivery_type: string | null;
  delivery_address: string | null;
  delivery_city: string | null;
  delivery_reference: string | null;
  client?: SalesInvoiceClient | null;
  client_branch?: SalesInvoiceClientBranch | null;
  sales_rep?: SalesInvoiceSalesRep | null;
  invoice_number: string;
  invoice_date: string;
  status: SalesInvoiceStatus;
  payment_status: SalesInvoicePaymentStatus;
  paid_amount: string;
  notes: string | null;
  total_cost: string | null;
  total_amount: string | null;
  margin_amount: string | null;
  created_at: string;
  items: SalesInvoiceItem[];
};

export type PaginatedSalesInvoicesResponse = {
  sales_invoices: SalesInvoice[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
};

export type CreateSalesInvoiceItemInput = {
  product_id: number;
  product_name: string;
  product_brand: string | null;
  product_sku: string | null;
  quantity: number;
};

export type CreateSalesInvoiceInput = {
  sales_type: SalesType;
  order_id?: number | null;
  client_id: number;
  client_branch_id?: number | null;
  invoice_number: string;
  invoice_date: string;
  notes?: string | null;
  items: CreateSalesInvoiceItemInput[];
};

export type UpdateSalesInvoiceStatusInput = {
  status: SalesInvoiceStatus;
};

export type SalesInvoicesQueryParams = {
  page?: number;
  page_size?: number;
  status?: SalesInvoiceStatus | "all";
};

export type ParsedSalesInvoiceItem = {
  product_name: string | null;
  quantity: number | null;
  unit_cost: string | null;
  unit_price: string | null;
  subtotal: string | null;
  confidence: number | null;
  warnings: string[];
};

export type SalesInvoiceImportPreviewResponse = {
  client_name: string | null;
  client_tax_id: string | null;
  invoice_number: string | null;
  invoice_date: string | null;
  total_amount: string | null;
  items: ParsedSalesInvoiceItem[];
  raw_text: string | null;
  warnings: string[];
  errors: string[];
};

export type SalesInvoiceImportCommitFileInput = {
  file: File;
  client_id?: number | null;
  client_branch_id?: number | null;
  notes?: string | null;
};

export type SalesInvoiceImportCommitItemInput = {
  product_id?: number | null;
  product_name?: string | null;
  product_sku?: string | null;
  quantity: number;
  unit_cost?: number | null;
  unit_price?: number | null;
  is_user_edited?: boolean;
};

export type SalesInvoiceImportCommitInput = {
  client_id?: number | null;
  client_branch_id?: number | null;
  client_name?: string | null;
  client_tax_id?: string | null;
  invoice_number: string;
  invoice_date: string;
  notes?: string | null;
  items: SalesInvoiceImportCommitItemInput[];
};