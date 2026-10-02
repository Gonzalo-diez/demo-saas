import { Badge } from "@/components/ui/badge";
import type { PurchaseInvoiceStatus } from "@/features/admin/purchase-invoices/types";

type PurchaseInvoiceStatusBadgeProps = {
  status: PurchaseInvoiceStatus;
};

const statusLabelMap: Record<PurchaseInvoiceStatus, string> = {
  draft: "Borrador",
  confirmed: "Confirmada",
  cancelled: "Cancelada",
};

export function PurchaseInvoiceStatusBadge({
  status,
}: PurchaseInvoiceStatusBadgeProps) {
  const variant =
    status === "confirmed"
      ? "default"
      : status === "cancelled"
        ? "destructive"
        : "secondary";

  return <Badge variant={variant}>{statusLabelMap[status]}</Badge>;
}