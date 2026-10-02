import { apiFetch, apiFetchBlob } from "@/lib/fetcher";
import {
  clientSalesLedgerResponseSchema,
  clientSalesSummaryResponseSchema,
  clientSaleRowSchema,
  supplierPurchaseRowSchema,
  supplierPurchasesLedgerResponseSchema,
} from "@/features/admin/account-ledger/schemas/account-ledger-schema";
import type {
  ClientSalesLedgerQueryParams,
  ClientSalesLedgerResponse,
  ClientSalesSummaryResponse,
  ClientSaleRow,
  LedgerPaymentCreateInput,
  LedgerPaymentUpdateInput,
  SupplierPurchaseRow,
  SupplierPurchasesLedgerQueryParams,
  SupplierPurchasesLedgerResponse,
} from "@/features/admin/account-ledger/types";

export async function getSupplierPurchasesLedgerApi(
  params: SupplierPurchasesLedgerQueryParams = {}
) {
  const searchParams = new URLSearchParams();

  if (params.sales_rep_id) {
    searchParams.set("sales_rep_id", String(params.sales_rep_id));
  }
  if (params.date_from) {
    searchParams.set("date_from", params.date_from);
  }
  if (params.date_to) {
    searchParams.set("date_to", params.date_to);
  }

  const data = await apiFetch<SupplierPurchasesLedgerResponse>(
    `/api/account-ledger/suppliers?${searchParams.toString()}`,
    { method: "GET" }
  );

  return supplierPurchasesLedgerResponseSchema.parse(data);
}

export async function getClientSalesLedgerApi(
  params: ClientSalesLedgerQueryParams = {}
) {
  const searchParams = new URLSearchParams();

  searchParams.set("page", String(params.page ?? 1));
  searchParams.set("page_size", String(params.page_size ?? 20));

  if (params.client_id) {
    searchParams.set("client_id", String(params.client_id));
  }
  if (params.sales_rep_id) {
    searchParams.set("sales_rep_id", String(params.sales_rep_id));
  }
  if (params.unassigned) {
    searchParams.set("unassigned", "true");
  }
  if (params.date_from) {
    searchParams.set("date_from", params.date_from);
  }
  if (params.date_to) {
    searchParams.set("date_to", params.date_to);
  }

  const data = await apiFetch<ClientSalesLedgerResponse>(
    `/api/account-ledger/clients?${searchParams.toString()}`,
    { method: "GET" }
  );

  return clientSalesLedgerResponseSchema.parse(data);
}

export async function getClientSalesSummaryApi(
  params: { date_from?: string | null; date_to?: string | null } = {}
) {
  const searchParams = new URLSearchParams();
  if (params.date_from) searchParams.set("date_from", params.date_from);
  if (params.date_to) searchParams.set("date_to", params.date_to);

  const data = await apiFetch<ClientSalesSummaryResponse>(
    `/api/account-ledger/clients/summary?${searchParams.toString()}`,
    { method: "GET" }
  );

  return clientSalesSummaryResponseSchema.parse(data);
}


// --------------- Proveedores: pagos ---------------

export async function addSupplierPaymentApi(
  purchaseInvoiceId: number,
  documentType: "purchase_invoice" | "purchase_quote",
  data: LedgerPaymentCreateInput
) {
  const response = await apiFetch<SupplierPurchaseRow>(
    `/api/account-ledger/suppliers/purchases/${purchaseInvoiceId}/payments/${documentType}`,
    { method: "POST", body: JSON.stringify(data) }
  );
  return supplierPurchaseRowSchema.parse(response);
}

export async function editSupplierPaymentApi(
  allocationId: number,
  data: LedgerPaymentUpdateInput
) {
  const response = await apiFetch<SupplierPurchaseRow>(
    `/api/account-ledger/suppliers/payments/${allocationId}`,
    { method: "PATCH", body: JSON.stringify(data) }
  );
  return supplierPurchaseRowSchema.parse(response);
}

export async function deleteSupplierPaymentApi(allocationId: number) {
  const response = await apiFetch<SupplierPurchaseRow>(
    `/api/account-ledger/suppliers/payments/${allocationId}`,
    { method: "DELETE" }
  );
  return supplierPurchaseRowSchema.parse(response);
}

// --------------- Clientes: pagos ---------------

export async function addClientPaymentApi(
  salesInvoiceId: number,
  documentType: "sales_invoice" | "sales_quote",
  data: LedgerPaymentCreateInput
) {
  const response = await apiFetch<ClientSaleRow>(
    `/api/account-ledger/clients/sales/${salesInvoiceId}/payments/${documentType}`,
    { method: "POST", body: JSON.stringify(data) }
  );
  return clientSaleRowSchema.parse(response);
}

export async function editClientPaymentApi(
  allocationId: number,
  data: LedgerPaymentUpdateInput
) {
  const response = await apiFetch<ClientSaleRow>(
    `/api/account-ledger/clients/payments/${allocationId}`,
    { method: "PATCH", body: JSON.stringify(data) }
  );
  return clientSaleRowSchema.parse(response);
}

export async function deleteClientPaymentApi(allocationId: number) {
  const response = await apiFetch<ClientSaleRow>(
    `/api/account-ledger/clients/payments/${allocationId}`,
    { method: "DELETE" }
  );
  return clientSaleRowSchema.parse(response);
}


// --------------- Exportar (Excel / PDF) ---------------

export type LedgerExportFormat = "xlsx" | "pdf";
export type LedgerExportTab = "suppliers" | "clients";

export async function exportLedgerApi(
  tab: LedgerExportTab,
  format: LedgerExportFormat,
  params: {
    sales_rep_id?: number | null;
    client_id?: number | null;
    date_from?: string | null;
    date_to?: string | null;
  } = {}
) {
  const searchParams = new URLSearchParams();
  searchParams.set("format", format);

  if (params.sales_rep_id) searchParams.set("sales_rep_id", String(params.sales_rep_id));
  if (params.client_id) searchParams.set("client_id", String(params.client_id));
  if (params.date_from) searchParams.set("date_from", params.date_from);
  if (params.date_to) searchParams.set("date_to", params.date_to);

  const blob = await apiFetchBlob(
    `/api/account-ledger/${tab}/export?${searchParams.toString()}`,
    { method: "GET" }
  );

  const extension = format === "xlsx" ? "xlsx" : "pdf";
  return { blob, filename: `cuenta-corriente-${tab}.${extension}` };
}

// --------------- Importar Excel ---------------

export async function importSupplierPurchasesApi(input: {
  file: File;
  salesRepId: number;
  supplierId: number;
  purchaseDate: string;
  sheetName?: string;
  dryRun: boolean;
}) {
  const formData = new FormData();
  formData.set("file", input.file);
  formData.set("sales_rep_id", String(input.salesRepId));
  formData.set("supplier_id", String(input.supplierId));
  formData.set("purchase_date", input.purchaseDate);
  if (input.sheetName) formData.set("sheet_name", input.sheetName);
  formData.set("dry_run", String(input.dryRun));

  return apiFetch<import("@/features/admin/account-ledger/types").SupplierImportResult>(
    "/api/account-ledger/import/suppliers",
    { method: "POST", body: formData }
  );
}

export async function importClientSalesApi(input: {
  file: File;
  sheetName?: string;
  dryRun: boolean;
}) {
  const formData = new FormData();
  formData.set("file", input.file);
  if (input.sheetName) formData.set("sheet_name", input.sheetName);
  formData.set("dry_run", String(input.dryRun));

  return apiFetch<import("@/features/admin/account-ledger/types").ClientImportResult>(
    "/api/account-ledger/import/clients",
    { method: "POST", body: formData }
  );
}