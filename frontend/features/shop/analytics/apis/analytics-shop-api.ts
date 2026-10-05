import { getApiUrl } from "@/lib/api";
import { tenantHeaders } from "@/lib/fetcher";
import type { AnalyticsEventType } from "@/features/admin/analytics/schemas/analytics-schema";

export interface CatalogEventCreate {
  visitor_id: string;
  session_id: string;
  event_type: AnalyticsEventType;
  product_id?: number;
  sales_rep_id?: number;
  source?: string;
  metadata_json?: Record<string, unknown>;
}

export async function trackCatalogEventApi(payload: CatalogEventCreate): Promise<void> {
  try {
    await fetch(`${getApiUrl()}/api/analytics/events`, {
      method: "POST",
      // X-Tenant-Domain: el visitante no tiene sesión, la tienda se sabe por el dominio.
      headers: { "Content-Type": "application/json", ...tenantHeaders() },
      body: JSON.stringify(payload),
    });
  } catch {
    // Silencioso: los errores de analytics nunca deben afectar al usuario
  }
}