"use client";

import Image from "next/image";
import { useEffect, useRef } from "react";
import { Plus } from "lucide-react";
import type { ShopProduct } from "@/features/shop/products/types";
import { useCartStore } from "@/store/cart-store";
import { QuantityStepper } from "@/features/shop/products/components/quantity-stepper";
import { useAnalyticsTracker } from "@/features/shop/analytics/hooks/use-analytics-tracker";

type Props = {
  product: ShopProduct;
  salesRepId?: number;
};

export function ProductCard({ product, salesRepId }: Props) {
  const { items, addItem, decreaseItem } = useCartStore();
  const { track } = useAnalyticsTracker();

  const cartItem = items.find((item) => item.id === product.id);
  const quantity = cartItem?.quantity ?? 0;

  // product_view: se dispara cuando la card entra al viewport (>50% visible)
  const cardRef = useRef<HTMLElement>(null);
  const hasTrackedView = useRef(false);

  useEffect(() => {
    const el = cardRef.current;
    if (!el) return;

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting && !hasTrackedView.current) {
          hasTrackedView.current = true;
          track({
            event_type: "product_view",
            product_id: product.id,
            sales_rep_id: salesRepId,
            source: "catalog",
          });
        }
      },
      { threshold: 0.5 },
    );

    observer.observe(el);
    return () => observer.disconnect();
  }, [product.id, salesRepId, track]);

  const handleAdd = () => {
    addItem(product);
    track({
      event_type: "product_click",
      product_id: product.id,
      sales_rep_id: salesRepId,
      source: "catalog",
      metadata_json: { action: "add_to_cart" },
    });
  };

  return (
    <article
      ref={cardRef}
      className="group flex h-full flex-col overflow-hidden rounded-xl border bg-card transition-shadow hover:shadow-md"
    >
      {/* Imagen */}
      <div className="relative flex h-40 w-full items-center justify-center bg-muted sm:h-48 md:h-52">
        {product.image_url ? (
          <Image
            src={product.image_url}
            alt={product.name}
            fill
            className="object-cover transition-transform duration-300 group-hover:scale-[1.03]"
            sizes="(max-width: 640px) 100vw, (max-width: 1024px) 50vw, 33vw"
          />
        ) : (
          <svg
            className="h-10 w-10 text-muted-foreground/40"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={1}
            aria-hidden="true"
          >
            <rect x="3" y="3" width="18" height="18" rx="2" strokeWidth="1.5" />
            <circle cx="8.5" cy="8.5" r="1.5" />
            <path d="M21 15l-5-5L5 21" strokeWidth="1.5" />
          </svg>
        )}

        {/* Badge de categoría sobre la imagen */}
        {product.category && (
          <span className="absolute left-2.5 top-2.5 rounded-full bg-card/90 px-2.5 py-0.5 text-[10px] font-semibold uppercase tracking-wider text-[var(--brand)] backdrop-blur-sm">
            {product.category}
          </span>
        )}
      </div>

      {/* Cuerpo */}
      <div className="flex flex-1 flex-col p-3 sm:p-4">
        <h3 className="line-clamp-2 min-h-[2.5rem] text-sm font-medium leading-snug sm:text-base">
          {product.name}
        </h3>

        <div className="space-y-3">
          <p className="text-lg font-bold sm:text-xl">
            ${product.unit_price.toLocaleString("es-AR")}
          </p>

          {quantity === 0 ? (
            <button
              type="button"
              onClick={handleAdd}
              className="flex w-full items-center justify-center gap-1.5 rounded-lg bg-foreground px-3 py-2 text-xs font-semibold text-background transition-opacity hover:opacity-80"
            >
              <Plus className="h-3.5 w-3.5" />
              Agregar
            </button>
          ) : (
            <div className="w-full">
              <QuantityStepper
                quantity={quantity}
                onDecrease={() => decreaseItem(product.id)}
                onIncrease={handleAdd}
              />
            </div>
          )}
        </div>
      </div>
    </article>
  );
}