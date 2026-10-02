import { Suspense } from "react";
import { DocumentsTabsPage } from "@/features/admin/documents/components/documents-tabs-page";

export default function PurchasesPage() {
  // useSearchParams (tab activo) requiere un límite de Suspense.
  return (
    <Suspense fallback={null}>
      <DocumentsTabsPage kind="purchases" />
    </Suspense>
  );
}
