import { apiFetch } from "@/lib/fetcher";
import { dashboardSummarySchema } from "../schemas/dashboard-schemas";

export async function getDashboardSummary() {
  const response = await apiFetch<unknown>("/api/dashboard/summary", {
    method: "GET",
  });

  return dashboardSummarySchema.parse(response);
}