import { apiFetch } from "@/lib/fetcher";
import type {
  AccountAgingSummary,
  AccountBalanceHistoryPoint,
  AccountBalanceSummary,
  AccountRankingItem,
  AccountRankingOrder,
  ClientAccountMovement,
  ClientAccountMovementsQueryParams,
  ClientAccountMovementsResponse,
  RegisterClientPaymentInput,
} from "@/features/admin/account-movements/types";

function buildClientAccountMovementsQuery(
  params: ClientAccountMovementsQueryParams = {}
) {
  const searchParams = new URLSearchParams();

  searchParams.set("page", String(params.page ?? 1));
  searchParams.set("page_size", String(params.page_size ?? 20));

  if (params.client_id) {
    searchParams.set("client_id", String(params.client_id));
  }

  if (params.movement_type && params.movement_type !== "all") {
    searchParams.set("movement_type", params.movement_type);
  }

  if (params.reference_type && params.reference_type !== "all") {
    searchParams.set("reference_type", params.reference_type);
  }

  return `/api/client-account-movements?${searchParams.toString()}`;
}

export async function getClientAccountMovementsApi(
  params: ClientAccountMovementsQueryParams = {}
) {
  return apiFetch<ClientAccountMovementsResponse>(
    buildClientAccountMovementsQuery(params),
    { method: "GET" }
  );
}

export async function getClientAccountMovementsByClientApi(
  clientId: number,
  page = 1,
  pageSize = 20
) {
  const searchParams = new URLSearchParams();
  searchParams.set("page", String(page));
  searchParams.set("page_size", String(pageSize));

  return apiFetch<ClientAccountMovementsResponse>(
    `/api/client-account-movements/by-client/${clientId}?${searchParams.toString()}`,
    { method: "GET" }
  );
}

export async function registerClientPaymentApi(
  clientId: number,
  data: RegisterClientPaymentInput
) {
  return apiFetch<ClientAccountMovement>(
    `/api/client-account-movements/by-client/${clientId}/payments`,
    {
      method: "POST",
      body: JSON.stringify(data),
    }
  );
}

export async function getClientBalanceSummaryApi() {
  return apiFetch<AccountBalanceSummary>(
    `/api/client-account-movements/stats/summary`,
    { method: "GET" }
  );
}

export async function getClientAgingSummaryApi() {
  return apiFetch<AccountAgingSummary>(
    `/api/client-account-movements/stats/aging`,
    { method: "GET" }
  );
}

export async function getClientRankingApi(
  order: AccountRankingOrder = "debtors",
  limit = 10
) {
  const searchParams = new URLSearchParams();
  searchParams.set("order", order);
  searchParams.set("limit", String(limit));

  return apiFetch<AccountRankingItem[]>(
    `/api/client-account-movements/stats/ranking?${searchParams.toString()}`,
    { method: "GET" }
  );
}

export async function getClientBalanceHistoryApi(clientId: number, limit = 60) {
  const searchParams = new URLSearchParams();
  searchParams.set("limit", String(limit));

  return apiFetch<AccountBalanceHistoryPoint[]>(
    `/api/client-account-movements/by-client/${clientId}/balance-history?${searchParams.toString()}`,
    { method: "GET" }
  );
}