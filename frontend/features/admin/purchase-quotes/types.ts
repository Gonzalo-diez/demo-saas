export type PurchaseQuoteStatus = "draft" | "sent" | "approved" | "rejected" | "expired";

export type DialogView = "manual" | "import";

export type PurchaseQuoteCreator = {
  id: number;
  name: string;
  email: string;
};

export type PurchaseQuoteItem = {
  id: number;
  product_id: number | null;
  product_name: string;
  product_sku: string | null;
  quantity: number;
  unit_cost: string;
  discount_amount: string;
  subtotal: string;
};

export type PurchaseQuotePaymentStatus = "pending" | "partial" | "paid";

export type PurchaseQuote = {
  id: number;
  supplier_id: number | null;
  supplier_name: string;
  supplier_tax_id: string | null;
  quote_number: string;
  quote_date: string;
  valid_until: string | null;
  status: PurchaseQuoteStatus;
  notes: string | null;
  total_amount: string | null;
  created_by: number | null;
  creator?: PurchaseQuoteCreator | null;
  items: PurchaseQuoteItem[];
  created_at: string;
  updated_at: string;
};

export type PaginatedPurchaseQuotesResponse = {
  purchase_quotes: PurchaseQuote[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
};

export type CreatePurchaseQuoteItemInput = {
  product_id?: number | null;
  product_name: string;
  product_sku?: string | null;
  quantity: number;
  unit_cost: number;
  discount_amount?: number;
};

export type CreatePurchaseQuoteInput = {
  supplier_id?: number | null;
  supplier_name?: string | null;
  supplier_tax_id?: string | null;
  quote_number: string;
  quote_date: string;
  valid_until?: string | null;
  notes?: string | null;
  items: CreatePurchaseQuoteItemInput[];
  force?: boolean;
};

export type UpdatePurchaseQuoteStatusInput = {
  status: PurchaseQuoteStatus;
};

export type PurchaseQuotesQueryParams = {
  page?: number;
  page_size?: number;
  status?: PurchaseQuoteStatus | "all";
  supplier_id?: number;
};

export type ParsedQuoteItem = {
  product_name: string | null;
  quantity: number | null;
  unit_cost: string | null;
  unit_price: string | null;
  subtotal: string | null;
  confidence: number | null;
  warnings: string[];
};

export type PurchaseQuoteImportPreviewResponse = {
  supplier_name: string | null;
  supplier_tax_id: string | null;
  quote_number: string | null;
  quote_date: string | null;
  total_amount: string | null;
  items: ParsedQuoteItem[];
  raw_text: string | null;
  warnings: string[];
  errors: string[];
};

export type PurchaseQuoteImportCommitFileInput = {
  file: File;
  supplier_id?: number | null;
  notes?: string | null;
};

export type PurchaseQuoteImportCommitItemInput = {
  product_id?: number | null;
  product_name?: string | null;
  product_sku?: string | null;
  quantity: number;
  unit_cost?: number | null;
  unit_price?: number | null;
  is_user_edited?: boolean;
};

export type PurchaseQuoteImportCommitInput = {
  supplier_name: string;
  supplier_tax_id: string | null;
  quote_number: string;
  quote_date: string;
  valid_until: string | null;
  notes?: string | null;
  items: PurchaseQuoteImportCommitItemInput[];
  force: boolean; 
};