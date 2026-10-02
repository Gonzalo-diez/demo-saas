export type SalesQuoteStatus =
  | "draft"
  | "sent"
  | "approved"
  | "rejected"
  | "expired"
  | "cancelled";

export type SalesType = "B2B" | "ONLINE";

export type DialogView = "manual" | "import";

export type SalesQuoteClient = {
  id: number;
  name: string;
  tax_id?: string | null;
};

export type SalesQuoteClientBranch = {
  id: number;
  name: string;
  address: string | null;
  city: string | null;
};

export type SalesQuoteSalesRep = {
  id: number;
  name: string;
  email: string;
};

export type SalesQuoteItem = {
  id: number;
  product_id: number | null;
  product_name: string;
  product_brand: string | null;
  product_sku: string | null;
  quantity: number;
  unit_cost: string | null;
  unit_price: string;
  discount_amount: string;
  subtotal_cost: string | null;
  subtotal: string;
  margin_amount: string | null;
};

export type SalesQuotePaymentStatus = "pending" | "partial" | "paid";

export type SalesQuote = {
  id: number;
  order_id: number | null;
  sales_type: SalesType;
  client_id: number | null;
  client_branch_id: number | null;
  client_name: string | null;
  client_tax_id: string | null;
  customer_phone: string | null;
  customer_email: string | null;
  delivery_type: string | null;
  delivery_address: string | null;
  delivery_city: string | null;
  delivery_reference: string | null;
  sales_rep_id: number | null;
  sales_rep?: SalesQuoteSalesRep | null;
  quote_number: string;
  quote_date: string;
  valid_until: string | null;
  status: SalesQuoteStatus;
  payment_method: string | null;
  payment_status: SalesQuotePaymentStatus;
  paid_amount: string;
  notes: string | null;
  total_cost: string | null;
  total_amount: string | null;
  margin_amount: string | null;
  currency: string;
  pdf_generated_at: string | null;
  email_sent_at: string | null;
  items: SalesQuoteItem[];
  created_at: string;
  updated_at: string;
};

export type PaginatedSalesQuotesResponse = {
  sales_quotes: SalesQuote[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
};

export type CreateSalesQuoteItemInput = {
  product_id?: number | null;
  product_name: string;
  product_sku?: string | null;
  quantity: number;
  unit_price: number;
  discount_amount?: number;
};

export type CreateSalesQuoteInput = {
  client_id?: number | null;
  client_branch_id?: number | null;
  client_name?: string | null;
  client_tax_id?: string | null;
  sales_rep_id?: number | null;
  quote_number: string;
  quote_date: string;
  valid_until?: string | null;
  payment_method?: string | null;
  notes?: string | null;
  items: CreateSalesQuoteItemInput[];
  force?: boolean;
};

export type UpdateSalesQuoteStatusInput = {
  status: SalesQuoteStatus;
};

export type SalesQuotesQueryParams = {
  page?: number;
  page_size?: number;
  status?: SalesQuoteStatus | "all";
  client_id?: number;
  from_orders?: boolean;
};

export type ParsedSalesQuoteItem = {
  product_name: string | null;
  quantity: number | null;
  unit_cost: string | null;
  unit_price: string | null;
  subtotal: string | null;
  confidence: number | null;
  warnings: string[];
};

export type SalesQuoteImportPreviewResponse = {
  client_name: string | null;
  client_tax_id: string | null;
  payment_method: string | null;
  quote_number: string | null;
  quote_date: string | null;
  total_amount: string | null;
  items: ParsedSalesQuoteItem[];
  raw_text: string | null;
  warnings: string[];
  errors: string[];
};

export type SalesQuoteImportCommitFileInput = {
  file: File;
  client_id?: number | null;
  client_branch_id?: number | null;
  notes?: string | null;
};

export type SalesQuoteImportCommitItemInput = {
  product_id?: number | null;
  product_name?: string | null;
  product_sku?: string | null;
  quantity: number;
  unit_cost?: number | null;
  unit_price?: number | null;
  is_user_edited?: boolean;
};

export type SalesQuoteImportCommitInput = {
  client_id?: number | null;
  client_branch_id?: number | null;
  client_name?: string | null;
  client_tax_id?: string | null;
  quote_number: string;
  quote_date: string;
  valid_until: string | null;
  notes?: string | null;
  items: SalesQuoteImportCommitItemInput[];
  force: boolean;
};