import { Badge } from "@/components/ui/badge";
import type { SalesInvoiceStatus } from "@/features/admin/sales-invoices/types";

type SalesInvoiceStatusBadgeProps = {
  status: SalesInvoiceStatus;
};

const statusLabelMap: Record<SalesInvoiceStatus, string> = {
  draft: "Borrador",
  confirmed: "Confirmada",
  cancelled: "Cancelada",
};

export function SalesInvoiceStatusBadge({
  status,
}: SalesInvoiceStatusBadgeProps) {
  const variant =
    status === "confirmed"
      ? "default"
      : status === "cancelled"
        ? "destructive"
        : "secondary";

  return <Badge variant={variant}>{statusLabelMap[status]}</Badge>
}