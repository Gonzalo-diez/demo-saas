import type { Metadata } from "next";
import { HeroCarousel } from "@/components/home/hero-carousel";

export const metadata: Metadata = {
  title: "Distri Choco - Distribuidora mayorista",
  description:
    "Distri Choco: distribuidora mayorista de cigarrillos, tabaco, farmacia y accesorios. Pedidos rápidos y entrega directa.",
};

export default function HomePage() {
  return (
    <main>
      <HeroCarousel />
    </main>
  );
}
