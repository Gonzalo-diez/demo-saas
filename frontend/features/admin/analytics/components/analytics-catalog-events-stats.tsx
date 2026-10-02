"use client";

import { useCatalogEventsCount } from "@/features/admin/analytics/hooks/use-analytics";
import type { AnalyticsEventType } from "@/features/admin/analytics/schemas/analytics-schema";

type Props = {
  targetDate: string;
};

const EVENT_LABELS: Partial<Record<AnalyticsEventType, string>> = {
  product_view: "Vistas de producto",
  product_click: "Clicks en producto",
  product_search: "Búsquedas",
  catalog_open: "Aperturas del catálogo",
};

// 1. Definimos los colores asociados a cada tipo de evento
const EVENT_COLORS: Partial<Record<AnalyticsEventType, string>> = {
  catalog_open: "bg-chart-3",
  product_view: "bg-chart-1",
  product_click: "bg-chart-2",
  product_search: "bg-stamp",
};

const EVENT_TYPES: AnalyticsEventType[] = [
  "catalog_open",
  "product_view",
  "product_click",
  "product_search",
];

function EventCountRow({
  targetDate,
  eventType,
  label,
  totalEvents,
  color, // Recibimos el color como prop
}: {
  targetDate: string;
  eventType: AnalyticsEventType;
  label: string;
  totalEvents: number;
  color: string;
}) {
  const { data: count, isLoading } = useCatalogEventsCount({
    start_date: `${targetDate}T00:00:00`,
    end_date: `${targetDate}T23:59:59`,
    event_type: eventType,
  });

  const pct =
    count !== undefined && totalEvents > 0
      ? Math.round((count / totalEvents) * 100)
      : 0;

  return (
    <div className="flex items-center gap-2 sm:gap-3">
      <span className="w-20 shrink-0 truncate text-xs text-muted-foreground sm:w-48 sm:text-sm">
        {label}
      </span>
      <div className="h-2 min-w-0 flex-1 overflow-hidden rounded-full bg-muted">
        {!isLoading && count !== undefined && (
          <div
            // 2. Aplicamos el color dinámico aquí
            className={`h-full rounded-full transition-all ${color}`}
            style={{ width: `${pct}%` }}
          />
        )}
      </div>
      <span className="w-9 shrink-0 text-right text-xs font-medium tabular-nums sm:w-12 sm:text-sm">
        {isLoading ? (
          <span className="inline-block h-4 w-8 rounded bg-muted" />
        ) : (
          (count ?? 0).toLocaleString("es-AR")
        )}
      </span>
    </div>
  );
}

export function AnalyticsCatalogEventsStats({ targetDate }: Props) {
  const { data: totalEvents = 0 } = useCatalogEventsCount({
    start_date: `${targetDate}T00:00:00`,
    end_date: `${targetDate}T23:59:59`,
  });

  return (
    <div className="rounded-xl border p-4 sm:p-5">
      <h2 className="mb-4 text-base font-semibold">Eventos de catálogo</h2>
      <div className="space-y-3">
        {EVENT_TYPES.map((type) => (
          <EventCountRow
            key={type}
            targetDate={targetDate}
            eventType={type}
            label={EVENT_LABELS[type]!}
            totalEvents={totalEvents}
            color={EVENT_COLORS[type] ?? "bg-muted-foreground"} // 3. Pasamos el color desde el mapa
          />
        ))}
      </div>
    </div>
  );
}