import { notFound } from "next/navigation";

import { ProductInventoryMovementsPageContent } from "@/features/admin/inventory-movements/components/product-inventory-movements-page-content";

type PageProps = {
  params: {
    id: string;
  };
};

export default function ProductInventoryMovementsPage({ params }: PageProps) {
  const productId = Number(params.id);

  if (!Number.isInteger(productId) || productId <= 0) {
    notFound();
  }

  return <ProductInventoryMovementsPageContent productId={productId} />;
}