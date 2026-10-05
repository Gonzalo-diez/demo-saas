import type { Metadata } from "next";
import { HeroCarousel } from "@/components/home/hero-carousel";

export const metadata: Metadata = {
  title: "Catálogo mayorista",
  description:
    "Catálogo mayorista online para comercios. Pedidos rápidos y entrega directa.",
};

export default function HomePage() {
  return (
    <main>
      <HeroCarousel />
    </main>
  );
}
