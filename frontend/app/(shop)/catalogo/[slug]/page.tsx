import { notFound } from "next/navigation";
import { Suspense } from "react";
import type { Metadata } from "next";
import { categories } from "@/types/categories";
import { RequireClientAuth } from "@/features/shop/auth/components/require-client-auth";
import { CatalogCategoryPageClient } from "@/app/(shop)/catalogo/[slug]/catalog-category-page-client";

type PageProps = {
  params: Promise<{ slug: string }>;
};

export function generateStaticParams() {
  return categories.map((category) => ({
    slug: category.slug,
  }));
}

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const { slug } = await params;
  const category = categories.find((item) => item.slug === slug);

  if (!category) {
    return {
      title: "Categoría no encontrada | Distri Choco",
      description: "La categoría solicitada no existe.",
    };
  }

  return {
    title: `${category.name} | Catálogo | Distri Choco`,
    description: category.description ?? `Catálogo de productos de ${category.name}.`,
  };
}

export default async function CatalogCategoryPage({ params }: PageProps) {
  const { slug } = await params;

  const category = categories.find((item) => item.slug === slug);
  if (!category) notFound();

  return (
    <Suspense fallback={null}>
      <RequireClientAuth>
        <CatalogCategoryPageClient category={category} />
      </RequireClientAuth>
    </Suspense>
  );
}