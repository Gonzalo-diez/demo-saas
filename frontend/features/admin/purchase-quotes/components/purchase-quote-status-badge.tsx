import { Badge } from "@/components/ui/badge";
import type { PurchaseQuoteStatus } from "@/features/admin/purchase-quotes/types";

type PurchaseQuoteStatusBadgeProps = {
  status: PurchaseQuoteStatus;
};

const statusLabelMap: Record<PurchaseQuoteStatus, string> = {
  draft: "Borrador",
  sent: "Enviado",
  approved: "Aprobado",
  rejected: "Rechazado",
  expired: "Expirado",
};

const statusVariantMap: Record<
  PurchaseQuoteStatus,
  "default" | "secondary" | "destructive" | "outline"
> = {
  draft: "secondary",
  sent: "outline",
  approved: "default",
  rejected: "destructive",
  expired: "destructive",
};

export function PurchaseQuoteStatusBadge({ status }: PurchaseQuoteStatusBadgeProps) {
  return <Badge variant={statusVariantMap[status]}>{statusLabelMap[status]}</Badge>;
}
