"use client";

import Link from "next/link";
import { Fragment, useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import type { Category } from "@/types/categories";
import { getProductsResponse } from "@/features/shop/products/apis/product-shop-api";
import { mapApiProductToProduct } from "@/features/shop/products/mappers";
import { getBrandOptions } from "@/lib/utils/get-filter-options";
import { CatalogFilters } from "@/features/shop/products/filters/catalog-filters";
import { ProductGrid } from "@/features/shop/products/components/product-grid";
import { MobileFilters } from "@/features/shop/products/filters/mobile-filters";
import { CatalogPagination } from "@/features/shop/products/components/catalog-pagination";
import { CatalogCategoryClient } from "@/app/(shop)/catalogo/[slug]/catalog-category-client";

type Props = {
  category: Category;
};

type ValidSort = "name-asc" | "name-desc" | "price-asc" | "price-desc";

const PAGE_SIZE = 24;

export function CatalogCategoryPageClient({ category }: Props) {
  const router = useRouter();
  const searchParams = useSearchParams();

  const rawSort = searchParams.get("sort");
  const validSort: ValidSort | undefined =
    rawSort === "name-asc" ||
    rawSort === "name-desc" ||
    rawSort === "price-asc" ||
    rawSort === "price-desc"
      ? rawSort
      : undefined;

  const salesRepId = searchParams.get("rep")
    ? Number(searchParams.get("rep"))
    : undefined;
  const currentPage = Math.max(1, Number(searchParams.get("page") || "1"));
  const search = searchParams.get("search") ?? undefined;
  const brand = searchParams.get("brand") ?? undefined;

  const query = { search, brand, sort: validSort };

  // Llamada principal (con filtros del usuario) + llamada "toda la
  // categoría" (para saber si tiene productos y armar las marcas),
  // igual que antes en el servidor.
  const mainQuery = useQuery({
    queryKey: [
      "shop-products",
      "category",
      category.value,
      search,
      brand,
      validSort,
      currentPage,
    ],
    queryFn: () =>
      getProductsResponse({
        is_active: true,
        category: category.value,
        search,
        brand,
        sort: validSort,
        page: currentPage,
        page_size: PAGE_SIZE,
      }),
  });

  const filtersQuery = useQuery({
    queryKey: ["shop-products", "category-all", category.value],
    queryFn: () =>
      getProductsResponse({
        is_active: true,
        category: category.value,
        page: 1,
        page_size: 100,
      }),
  });

  const response = mainQuery.data;
  const totalPages = response
    ? Math.max(1, Math.ceil(response.total / response.page_size))
    : 1;

  // Si la página pedida quedó fuera de rango (ej. cambiaron los
  // filtros), volvemos a la última página válida.
  useEffect(() => {
    if (response && currentPage > totalPages && totalPages > 0) {
      const params = new URLSearchParams(searchParams.toString());
      params.set("page", String(totalPages));
      router.replace(`/catalogo/${category.slug}?${params.toString()}`);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [response, currentPage, totalPages]);

  if (mainQuery.isLoading || filtersQuery.isLoading) {
    return (
      <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 sm:py-10">
        <p className="text-sm text-muted-foreground">Cargando productos...</p>
      </main>
    );
  }

  if (!response || !filtersQuery.data) {
    return (
      <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 sm:py-10">
        <div className="rounded-2xl border border-dashed bg-card p-8 text-center">
          <h2 className="text-lg font-semibold">No pudimos cargar el catálogo</h2>
          <p className="mt-2 text-sm text-muted-foreground">
            Probá recargando la página en unos segundos.
          </p>
        </div>
      </main>
    );
  }

  const products = response.items;
  const filterProducts = filtersQuery.data.items.map(mapApiProductToProduct);
  const categoryHasProducts = filtersQuery.data.total > 0;
  const brands = getBrandOptions(filterProducts);

  return (
    <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 sm:py-10">
      <CatalogCategoryClient categorySlug={category.slug} salesRepId={salesRepId} />

      <div className="mb-8">
        <Link
          href="/"
          className="mb-4 inline-flex text-sm text-muted-foreground transition hover:text-foreground"
        >
          ← Volver al inicio
        </Link>

        <h1 className="text-3xl font-bold sm:text-4xl">{category.name}</h1>

        {category.description && (
          <p className="mt-2 max-w-3xl text-sm text-muted-foreground sm:text-base">
            {category.description}
          </p>
        )}

        <div className="mt-4 text-sm text-muted-foreground">
          {response.total} producto{response.total !== 1 ? "s" : ""}
          {totalPages > 1 && (
            <Fragment>
              {" "}
              • Página {response.page} de {totalPages}
            </Fragment>
          )}
        </div>
      </div>

      {!categoryHasProducts ? (
        <div className="rounded-2xl border border-dashed bg-card p-8 text-center">
          <h2 className="text-lg font-semibold">No hay productos cargados</h2>
          <p className="mt-2 text-sm text-muted-foreground">
            Esta categoría todavía no tiene productos asociados.
          </p>
        </div>
      ) : (
        <Fragment>
          <div className="mb-4 flex items-center justify-between lg:hidden">
            <MobileFilters brands={brands} currentFilters={query} salesRepId={salesRepId} />
          </div>

          <div className="grid gap-8 lg:grid-cols-[280px_1fr]">
            <div className="hidden lg:block">
              <CatalogFilters brands={brands} currentFilters={query} salesRepId={salesRepId} />
            </div>

            {products.length === 0 ? (
              <div className="rounded-2xl border border-dashed bg-card p-8 text-center">
                <h2 className="text-lg font-semibold">No se encontraron productos</h2>
                <p className="mt-2 text-sm text-muted-foreground">
                  Prueba cambiando o limpiando los filtros.
                </p>
              </div>
            ) : (
              <div className="space-y-6">
                <ProductGrid products={products} salesRepId={salesRepId} />
                <CatalogPagination currentPage={response.page} totalPages={totalPages} />
              </div>
            )}
          </div>
        </Fragment>
      )}
    </main>
  );
}