import { Badge } from "@/components/ui/badge";
import type { OrderStatus } from "@/features/admin/orders/types";

const statusConfig: Record<OrderStatus, { label: string; className: string }> = {
  pending_confirmation: { label: "Pendiente", className: "bg-kraft/15 text-kraft border-kraft/20" },
  confirmed: { label: "Confirmado", className: "bg-chart-3/15 text-chart-3 border-chart-3/20" },
  preparing: { label: "Preparando", className: "bg-chart-4/15 text-chart-4 border-chart-4/20" },
  shipped: { label: "Enviado", className: "bg-chart-5/15 text-chart-5 border-chart-5/20" },
  delivered: { label: "Entregado", className: "bg-brand-muted text-brand border-brand/20" },
  cancelled: { label: "Cancelado", className: "bg-destructive/15 text-destructive border-destructive/20" },
};

export function OrderStatusBadge({ status }: { status: OrderStatus }) {
  const config = statusConfig[status];

  return (
    <Badge variant="outline" className={config.className}>
      {config.label}
    </Badge>
  );
}