import { Suspense } from "react";
import type { Metadata } from "next";
import { CatalogCategoryRoute } from "@/app/(shop)/catalogo/[slug]/catalog-category-route";

type PageProps = {
  params: Promise<{ slug: string }>;
};

export const metadata: Metadata = {
  title: "Categoría | Catálogo",
};

export default async function CatalogCategoryPage({ params }: PageProps) {
  const { slug } = await params;

  // Público: se puede mirar sin cuenta. La cuenta se pide al finalizar la compra.
  return (
    <Suspense fallback={null}>
      <CatalogCategoryRoute slug={slug} />
    </Suspense>
  );
}
