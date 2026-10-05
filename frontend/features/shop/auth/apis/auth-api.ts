import { apiFetch } from "@/lib/fetcher";
import type {
  ClientLoginInput,
  ClientRegisterInput,
  ClientUser,
  MessageResponse,
} from "@/features/shop/auth/types";

export async function loginClientApi(
  data: ClientLoginInput
): Promise<ClientUser> {
  return apiFetch<ClientUser>("/api/clients/login", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

/** Alta de un cliente desde la tienda; deja la sesión iniciada (cookie). */
export async function registerClientApi(
  data: ClientRegisterInput
): Promise<ClientUser> {
  return apiFetch<ClientUser>("/api/clients/register", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function logoutClientApi(): Promise<MessageResponse> {
  return apiFetch<MessageResponse>("/api/clients/logout", {
    method: "POST",
  });
}

export async function getClientMeApi(): Promise<ClientUser> {
  return apiFetch<ClientUser>("/api/clients/me");
}