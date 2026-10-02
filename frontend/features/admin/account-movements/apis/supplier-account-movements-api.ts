import { apiFetch } from "@/lib/fetcher";
import type {
  AccountAgingSummary,
  AccountBalanceHistoryPoint,
  AccountBalanceSummary,
  AccountRankingItem,
  AccountRankingOrder,
  RegisterSupplierPaymentInput,
  SupplierAccountMovement,
  SupplierAccountMovementsQueryParams,
  SupplierAccountMovementsResponse,
} from "@/features/admin/account-movements/types";

function buildSupplierAccountMovementsQuery(
  params: SupplierAccountMovementsQueryParams = {}
) {
  const searchParams = new URLSearchParams();

  searchParams.set("page", String(params.page ?? 1));
  searchParams.set("page_size", String(params.page_size ?? 20));

  if (params.supplier_id) {
    searchParams.set("supplier_id", String(params.supplier_id));
  }

  if (params.movement_type && params.movement_type !== "all") {
    searchParams.set("movement_type", params.movement_type);
  }

  if (params.reference_type && params.reference_type !== "all") {
    searchParams.set("reference_type", params.reference_type);
  }

  return `/api/supplier-account-movements?${searchParams.toString()}`;
}

export async function getSupplierAccountMovementsApi(
  params: SupplierAccountMovementsQueryParams = {}
) {
  return apiFetch<SupplierAccountMovementsResponse>(
    buildSupplierAccountMovementsQuery(params),
    { method: "GET" }
  );
}

export async function getSupplierAccountMovementsBySupplierApi(
  supplierId: number,
  page = 1,
  pageSize = 20
) {
  const searchParams = new URLSearchParams();
  searchParams.set("page", String(page));
  searchParams.set("page_size", String(pageSize));

  return apiFetch<SupplierAccountMovementsResponse>(
    `/api/supplier-account-movements/by-supplier/${supplierId}?${searchParams.toString()}`,
    { method: "GET" }
  );
}

export async function registerSupplierPaymentApi(
  supplierId: number,
  data: RegisterSupplierPaymentInput
) {
  return apiFetch<SupplierAccountMovement>(
    `/api/supplier-account-movements/by-supplier/${supplierId}/payments`,
    {
      method: "POST",
      body: JSON.stringify(data),
    }
  );
}

export async function getSupplierBalanceSummaryApi() {
  return apiFetch<AccountBalanceSummary>(
    `/api/supplier-account-movements/stats/summary`,
    { method: "GET" }
  );
}

export async function getSupplierAgingSummaryApi() {
  return apiFetch<AccountAgingSummary>(
    `/api/supplier-account-movements/stats/aging`,
    { method: "GET" }
  );
}

export async function getSupplierRankingApi(
  order: AccountRankingOrder = "debtors",
  limit = 10
) {
  const searchParams = new URLSearchParams();
  searchParams.set("order", order);
  searchParams.set("limit", String(limit));

  return apiFetch<AccountRankingItem[]>(
    `/api/supplier-account-movements/stats/ranking?${searchParams.toString()}`,
    { method: "GET" }
  );
}

export async function getSupplierBalanceHistoryApi(supplierId: number, limit = 60) {
  const searchParams = new URLSearchParams();
  searchParams.set("limit", String(limit));

  return apiFetch<AccountBalanceHistoryPoint[]>(
    `/api/supplier-account-movements/by-supplier/${supplierId}/balance-history?${searchParams.toString()}`,
    { method: "GET" }
  );
}