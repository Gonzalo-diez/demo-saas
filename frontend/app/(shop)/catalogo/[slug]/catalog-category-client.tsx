"use client";

import { useEffect } from "react";
import { useAnalyticsTracker } from "@/features/shop/analytics/hooks/use-analytics-tracker";

type Props = {
  categorySlug: string;
  salesRepId?: number;
};

/**
 * Componente cliente liviano que dispara catalog_open al montar la página.
 * Se usa dentro del Server Component de la página para no perder SSR.
 */
export function CatalogCategoryClient({ categorySlug, salesRepId }: Props) {
  const { track } = useAnalyticsTracker();

  useEffect(() => {
    track({
      event_type: "catalog_open",
      sales_rep_id: salesRepId,
      source: "catalog",
      metadata_json: { category_slug: categorySlug },
    });
  // Solo al montar (apertura de la categoría)
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return null;
}