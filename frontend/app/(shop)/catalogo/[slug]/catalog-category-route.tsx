"use client";

import Link from "next/link";
import { useShopCategories } from "@/features/shop/categories/hooks/use-shop-categories";
import { CatalogCategoryPageClient } from "@/app/(shop)/catalogo/[slug]/catalog-category-page-client";

/**
 * Las categorías son de cada distribuidora y se leen de la API, así que el
 * slug de la URL se resuelve en el cliente (no hay lista fija en el build).
 */
export function CatalogCategoryRoute({ slug }: { slug: string }) {
  const { data, isLoading, isError } = useShopCategories();

  if (isLoading) {
    return (
      <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 sm:py-10">
        <p className="text-sm text-muted-foreground">Cargando categoría...</p>
      </main>
    );
  }

  const category = data?.items.find((item) => item.slug === slug);

  if (isError || !category) {
    return (
      <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 sm:py-10">
        <div className="rounded-3xl border border-dashed bg-card p-8 text-center">
          <h1 className="text-xl font-bold">Categoría no encontrada</h1>
          <p className="mt-2 text-sm text-muted-foreground">
            La categoría que buscás no existe o ya no está publicada.
          </p>
          <Link
            href="/catalogo"
            className="mt-4 inline-flex text-sm font-semibold text-brand hover:underline"
          >
            ← Volver al catálogo
          </Link>
        </div>
      </main>
    );
  }

  return <CatalogCategoryPageClient category={category} />;
}
