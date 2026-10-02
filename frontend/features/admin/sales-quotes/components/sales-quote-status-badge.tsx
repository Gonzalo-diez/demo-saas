import { Badge } from "@/components/ui/badge";
import type { SalesQuoteStatus } from "@/features/admin/sales-quotes/types";

type SalesQuoteStatusBadgeProps = {
  status: SalesQuoteStatus;
};

const statusLabelMap: Record<SalesQuoteStatus, string> = {
  draft: "Borrador",
  sent: "Enviado",
  approved: "Aprobado",
  rejected: "Rechazado",
  expired: "Expirado",
  cancelled: "Cancelado",
};

const statusVariantMap: Record<
  SalesQuoteStatus,
  "default" | "secondary" | "destructive" | "outline"
> = {
  draft: "secondary",
  sent: "outline",
  approved: "default",
  rejected: "destructive",
  expired: "destructive",
  cancelled: "destructive",
};

export function SalesQuoteStatusBadge({ status }: SalesQuoteStatusBadgeProps) {
  return <Badge variant={statusVariantMap[status]}>{statusLabelMap[status]}</Badge>;
}
