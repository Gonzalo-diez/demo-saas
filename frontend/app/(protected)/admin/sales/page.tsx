import { Suspense } from "react";
import { DocumentsTabsPage } from "@/features/admin/documents/components/documents-tabs-page";

export default function SalesPage() {
  // useSearchParams (tab activo) requiere un límite de Suspense.
  return (
    <Suspense fallback={null}>
      <DocumentsTabsPage kind="sales" />
    </Suspense>
  );
}
