import { apiFetch } from "@/lib/fetcher";
import type {
  RegisterSalesInvoicePaymentInput,
  SalesInvoicePaymentsResponse,
} from "@/features/admin/account-movements/types";

export async function getSalesInvoicePaymentsApi(salesInvoiceId: number) {
  return apiFetch<SalesInvoicePaymentsResponse>(
    `/api/sales-invoices/${salesInvoiceId}/payments`,
    { method: "GET" }
  );
}

export async function registerSalesInvoicePaymentApi(
  salesInvoiceId: number,
  data: RegisterSalesInvoicePaymentInput
) {
  return apiFetch<SalesInvoicePaymentsResponse>(
    `/api/sales-invoices/${salesInvoiceId}/payments`,
    {
      method: "POST",
      body: JSON.stringify(data),
    }
  );
}