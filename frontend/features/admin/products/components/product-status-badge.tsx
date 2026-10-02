import { Badge } from "@/components/ui/badge";
import type { ProductStatusFilter } from "@/features/admin/products/types";

type ProductStatusBadgeProps = {
  status: ProductStatusFilter;
};

export function ProductStatusBadge({
  status,
}: ProductStatusBadgeProps) {
  return (
    <Badge variant={status === "active" ? "default" : "secondary"}>
      {status === "active" ? "Activo" : status === "inactive" ? "Inactivo" : "Borrador"}
    </Badge>
  );
}