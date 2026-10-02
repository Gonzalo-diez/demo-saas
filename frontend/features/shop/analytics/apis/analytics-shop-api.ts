import { API_URL } from "@/lib/api";
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
    await fetch(`${API_URL}/api/analytics/events`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
  } catch {
    // Silencioso: los errores de analytics nunca deben afectar al usuario
  }
}