import type { Metadata } from "next";
import { Suspense } from "react";
import { HeroCarousel } from "@/components/home/hero-carousel";
import { CategoryGrid } from "@/features/shop/products/components/category-grid";
import { RequireClientAuth } from "@/features/shop/auth/components/require-client-auth";

export const metadata: Metadata = {
  title: "Catálogo | Distri Choco",
  description: "Catálogo mayorista de Distri Choco.",
};

export default function CatalogoPage() {
  return (
    <Suspense fallback={null}>
      <RequireClientAuth>
        <main>
          <HeroCarousel />
          <CategoryGrid />
        </main>
      </RequireClientAuth>
    </Suspense>
  );
}
