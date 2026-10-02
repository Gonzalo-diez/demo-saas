import { apiFetch } from "@/lib/fetcher";
import type { AuthUser, LoginInput, MessageResponse } from "../types";

export async function loginApi(data: LoginInput) {
  return apiFetch<AuthUser>("/api/sales-reps/login", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function getMeApi() {
  return apiFetch<AuthUser>("/api/sales-reps/me", {
    method: "GET",
  });
}

export async function logoutApi() {
  return apiFetch<MessageResponse>("/api/sales-reps/logout", {
    method: "POST",
  });
}