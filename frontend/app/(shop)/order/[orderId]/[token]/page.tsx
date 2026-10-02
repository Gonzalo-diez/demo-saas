import type { Metadata } from "next";
import { EditOrderClient } from "@/features/shop/orders/components/edit-order-client";

type PageProps = {
  params: Promise<{ orderId: string }>;
  searchParams: Promise<{ token?: string }>;
};

export async function generateMetadata(): Promise<Metadata> {
  return {
    title: "Editar pedido | Distri Choco",
    description: "Agregá o quitá productos de tu pedido.",
    robots: { index: false, follow: false },
  };
}

export default async function EditOrderPage({ params, searchParams }: PageProps) {
  const { orderId } = await params;
  const { token } = await searchParams;

  const parsedOrderId = Number(orderId);

  if (!Number.isInteger(parsedOrderId) || parsedOrderId <= 0 || !token) {
    return (
      <main className="mx-auto max-w-3xl px-4 py-12 text-center">
        <h1 className="text-xl font-semibold">Link inválido</h1>
        <p className="mt-2 text-sm text-muted-foreground">
          Este link no es válido. Pedí uno nuevo escribiéndonos por WhatsApp.
        </p>
      </main>
    );
  }

  return <EditOrderClient orderId={parsedOrderId} token={token} />;
}