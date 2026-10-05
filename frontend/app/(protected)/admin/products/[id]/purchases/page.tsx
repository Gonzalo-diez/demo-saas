import { notFound } from "next/navigation";
import { ProductPurchasesPageContent } from "@/features/admin/products/components/product-purchases-page-content";

type PageProps = {
  params: Promise<{ id: string }>;
};

export default async function ProductPurchasesPage({ params }: PageProps) {
  const { id } = await params;
  const productId = Number(id);

  if (!Number.isInteger(productId) || productId <= 0) {
    notFound();
  }

  return <ProductPurchasesPageContent productId={productId} />;
}
