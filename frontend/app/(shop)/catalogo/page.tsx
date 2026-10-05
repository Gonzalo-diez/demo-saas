import type { Metadata } from "next";
import { HeroCarousel } from "@/components/home/hero-carousel";
import { CategoryGrid } from "@/features/shop/products/components/category-grid";

export const metadata: Metadata = {
  title: "Catálogo",
  description: "Catálogo mayorista online.",
};

// El catálogo es público: se puede mirar sin cuenta. La cuenta se pide recién al
// finalizar la compra (checkout).
export default function CatalogoPage() {
  return (
    <main>
      <HeroCarousel />
      <CategoryGrid />
    </main>
  );
}
