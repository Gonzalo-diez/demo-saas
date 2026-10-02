import { apiFetch } from "@/lib/fetcher";
import type {
  CreateOrderB2BInput,
  AdminOrder,
  AdminOrderQueryParams,
  PaginatedAdminOrdersResponse,
  UpdateOrderStatusInput,
  UpdateOrderB2BInput,
  EditOrderB2BInput,
  EditOrderShopInput,
  OrderScheduleDelivery,
} from "@/features/admin/orders/types";

function buildOrdersQuery(params: AdminOrderQueryParams = {}) {
  const searchParams = new URLSearchParams();

  searchParams.set("page", String(params.page ?? 1));
  searchParams.set("page_size", String(params.page_size ?? 20));

  if (params.status) {
    searchParams.set("status", params.status);
  }

  if (params.client_id) {
    searchParams.set("client_id", String(params.client_id));
  }

  return `/api/orders?${searchParams.toString()}`;
}

export async function getOrdersApi(params: AdminOrderQueryParams = {}) {
  return apiFetch<PaginatedAdminOrdersResponse>(buildOrdersQuery(params), {
    method: "GET",
  });
}

export async function getOrderByIdApi(orderId: number) {
  return apiFetch<AdminOrder>(`/api/orders/${orderId}`, {
    method: "GET",
  });
}

export async function createOrderB2BApi(data: CreateOrderB2BInput) {
  return apiFetch<AdminOrder>("/api/orders/b2b", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function updateOrderB2BApi(orderId: number, data: UpdateOrderB2BInput) {
  return apiFetch<AdminOrder>(`/api/orders/b2b/${orderId}`, {
    method: "PUT",
    body: JSON.stringify(data),
  });
}

export async function updateOrderStatusApi(
  orderId: number,
  data: UpdateOrderStatusInput // Ahora data solo tiene { status: OrderStatus }
) {
  return apiFetch<AdminOrder>(`/api/orders/${orderId}/status`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export async function editOrderB2BApi(orderId: number, data: EditOrderB2BInput) {
  return apiFetch<AdminOrder>(`/api/orders/b2b/${orderId}/edit`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export async function editOrderShopApi(orderId: number, data: EditOrderShopInput) {
  return apiFetch<AdminOrder>(`/api/orders/shop/${orderId}/edit`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export async function scheduleDeliveryApi(orderId: number, data: OrderScheduleDelivery) {
  return apiFetch<AdminOrder>(`/api/orders/${orderId}/schedule-delivery`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}