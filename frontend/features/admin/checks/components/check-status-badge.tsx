import { Badge } from "@/components/ui/badge";
import type { CheckStatus } from "@/features/admin/checks/types";

type CheckStatusBadgeProps = {
  status: CheckStatus;
};

const statusLabelMap: Record<CheckStatus, string> = {
  pendiente: "Pendiente",
  depositado: "Depositado",
  acreditado: "Acreditado",
  rechazado: "Rechazado",
};

const statusVariantMap: Record<CheckStatus, "default" | "secondary" | "destructive" | "outline"> = {
  pendiente: "secondary",
  depositado: "outline",
  acreditado: "default",
  rechazado: "destructive",
};

export function CheckStatusBadge({ status }: CheckStatusBadgeProps) {
  return <Badge variant={statusVariantMap[status]}>{statusLabelMap[status]}</Badge>;
}
