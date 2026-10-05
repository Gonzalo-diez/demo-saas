"use client";

import { useQuery } from "@tanstack/react-query";
import { ProductCategoryCard } from "@/features/shop/products/components/product-category-card";
import { useShopCategories } from "@/features/shop/categories/hooks/use-shop-categories";
import { getAllProducts } from "@/features/shop/products/apis/product-shop-api";
import { mapApiProductToProduct } from "@/features/shop/products/mappers";

export function CategoryGrid() {
  const categoriesQuery = useShopCategories();

  const { data: apiProducts } = useQuery({
    queryKey: ["shop-products", "all-active"],
    queryFn: () => getAllProducts({ is_active: true }),
    staleTime: 1000 * 60,
  });

  const products = (apiProducts ?? []).map(mapApiProductToProduct);
  const categories = categoriesQuery.data?.items ?? [];

  return (
    <section className="mx-auto max-w-7xl px-4 py-8 sm:px-6 sm:py-10">
      <div className="mb-6">
        <h2 className="font-heading text-2xl font-extrabold sm:text-3xl">
          Catálogos
        </h2>
        <p className="mt-2 text-sm text-muted-foreground sm:text-base">
          Elegí una categoría para ver sus productos.
        </p>
      </div>

      {categoriesQuery.isLoading ? (
        <p className="text-sm text-muted-foreground">Cargando categorías...</p>
      ) : categoriesQuery.isError ? (
        <div className="rounded-3xl border border-dashed bg-card p-8 text-center">
          <h3 className="text-lg font-semibold">No pudimos cargar las categorías</h3>
          <p className="mt-2 text-sm text-muted-foreground">
            Probá recargando la página en unos segundos.
          </p>
        </div>
      ) : categories.length === 0 ? (
        <div className="rounded-3xl border border-dashed bg-card p-8 text-center">
          <h3 className="text-lg font-semibold">Todavía no hay catálogo disponible</h3>
          <p className="mt-2 text-sm text-muted-foreground">
            Esta distribuidora aún no publicó categorías.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
          {categories.map((category) => {
            const count = products.filter(
              (product) => product.categoryId === category.id,
            ).length;

            return (
              <ProductCategoryCard
                key={category.id}
                title={category.name}
                description={category.description ?? undefined}
                image_url={category.image_url ?? undefined}
                href={`/catalogo/${category.slug}`}
                count={count}
                ageRestricted={category.requires_age_verification}
              />
            );
          })}
        </div>
      )}
    </section>
  );
}
