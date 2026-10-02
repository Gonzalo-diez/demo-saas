"use client";

import { useQuery } from "@tanstack/react-query";
import { ProductCategoryCard } from "@/features/shop/products/components/product-category-card";
import { categories } from "@/types/categories";
import { getAllProducts } from "@/features/shop/products/apis/product-shop-api";
import { mapApiProductToProduct } from "@/features/shop/products/mappers";

export function CategoryGrid() {
  const { data: apiProducts } = useQuery({
    queryKey: ["shop-products", "all-active"],
    queryFn: () => getAllProducts({ is_active: true }),
    staleTime: 1000 * 60,
  });

  const products = (apiProducts ?? []).map(mapApiProductToProduct);

  return (
    <section className="mx-auto max-w-7xl px-4 py-8 sm:px-6 sm:py-10">
      <div className="mb-6">
        <h2 className="font-heading text-2xl font-black sm:text-3xl">
          Catálogos
        </h2>
        <p className="mt-2 text-sm text-muted-foreground sm:text-base">
          Elegí una categoría para ver sus productos.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {categories.map((category) => {
          const count = products.filter(
            (product) => product.categorySlug === category.slug,
          ).length;

          return (
            <ProductCategoryCard
              key={category.slug}
              title={category.name}
              description={category.description}
              href={`/catalogo/${category.slug}`}
              count={count}
              image_url={category.image_url}
            />
          );
        })}
      </div>
    </section>
  );
}