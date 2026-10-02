"use client";

import { useRef, useCallback } from "react";
import type { AnalyticsEventType } from "@/features/admin/analytics/schemas/analytics-schema";
import { trackCatalogEventApi } from "@/features/shop/analytics/apis/analytics-shop-api";

function getOrCreate(storage: Storage, key: string): string {
  const existing = storage.getItem(key);
  if (existing) return existing;
  const id = crypto.randomUUID();
  storage.setItem(key, id);
  return id;
}

export function getVisitorId(): string {
  try { return getOrCreate(localStorage, "analytics_visitor_id"); }
  catch { return "unknown"; }
}

export function getSessionId(): string {
  try { return getOrCreate(sessionStorage, "analytics_session_id"); }
  catch { return "unknown"; }
}

export interface TrackEventPayload {
  event_type: AnalyticsEventType;
  product_id?: number;
  sales_rep_id?: number;
  source?: string;
  metadata_json?: Record<string, unknown>;
}

export function useAnalyticsTracker() {
  // Evita re-renders innecesarios con useRef para el estado del debounce
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const track = useCallback((data: TrackEventPayload) => {
    trackCatalogEventApi({
      visitor_id: getVisitorId(),
      session_id: getSessionId(),
      ...data,
    });
  }, []);

  const trackDebounced = useCallback((data: TrackEventPayload, delay = 800) => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    if (!("metadata_json" in data) || (data.metadata_json as Record<string, unknown>)?.query) {
      debounceRef.current = setTimeout(() => {
        trackCatalogEventApi({
          visitor_id: getVisitorId(),
          session_id: getSessionId(),
          ...data,
        });
      }, delay);
    }
  }, []);

  return { track, trackDebounced };
}