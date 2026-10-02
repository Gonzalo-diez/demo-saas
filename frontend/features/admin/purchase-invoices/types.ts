export type PurchaseInvoiceStatus = "draft" | "confirmed" | "cancelled";

export type DialogView = "manual" | "import";

export type PurchaseInvoiceCreator = {
  id: number;
  name: string;
  email: string;
};

export type PurchaseInvoiceItem = {
  id: number;
  product_id: number | null;
  product_name: string;
  product_sku: string | null;
  quantity: number;
  unit_cost: string;
  subtotal: string;
};

export type PurchaseInvoicePaymentStatus = "pending" | "partial" | "paid";

export type PurchaseInvoice = {
  id: number;
  supplier_id: number | null;
  supplier_name: string;
  supplier_tax_id: string | null;
  invoice_number: string;
  invoice_date: string;
  status: PurchaseInvoiceStatus;
  payment_status: PurchaseInvoicePaymentStatus;
  paid_amount: string;
  notes: string | null;
  total_amount: string | null;
  created_by: number | null;
  created_at: string;
  creator?: PurchaseInvoiceCreator | null;
  items: PurchaseInvoiceItem[];
};

export type PurchaseInvoicesResponse = {
  purchase_invoices: PurchaseInvoice[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
};

export type CreatePurchaseInvoiceItemInput = {
  product_id: number | null;
  product_name: string;
  product_sku?: string | null;
  quantity: number;
  unit_cost: number;
};

export type CreatePurchaseInvoiceInput = {
  supplier_id?: number | null;
  supplier_name?: string | null;
  supplier_tax_id?: string | null;
  invoice_number: string;
  invoice_date: string;
  notes?: string | null;
  items: CreatePurchaseInvoiceItemInput[];
};

export type UpdatePurchaseInvoiceStatusInput = {
  status: PurchaseInvoiceStatus;
};

export type PurchaseInvoicesQueryParams = {
  page?: number;
  page_size?: number;
  status?: PurchaseInvoiceStatus | "all";
};

export type ParsedInvoiceItem = {
  product_name: string | null;
  quantity: number | null;
  unit_cost: string | null;
  unit_price: string | null;
  subtotal: string | null;
  confidence: number | null;
  warnings: string[];
};

export type PurchaseInvoiceImportPreviewResponse = {
  supplier_name: string | null;
  supplier_tax_id: string | null;
  invoice_number: string | null;
  invoice_date: string | null;
  total_amount: string | null;
  items: ParsedInvoiceItem[];
  raw_text: string | null;
  warnings: string[];
  errors: string[];
};

export type PurchaseInvoiceImportCommitFileInput = {
  file: File;
  supplier_id?: number | null;
  notes?: string | null;
};

export type PurchaseInvoiceImportCommitItemInput = {
  product_id?: number | null;
  product_name?: string | null;
  product_sku?: string | null;
  quantity: number;
  unit_cost?: number | null;
  unit_price?: number | null;
  is_user_edited?: boolean;
};

export type PurchaseInvoiceImportCommitInput = {
  supplier_name: string;
  supplier_tax_id?: string | null;
  invoice_number: string;
  invoice_date: string;
  notes?: string | null;
  items: PurchaseInvoiceImportCommitItemInput[];
};