import { Badge } from "@/components/ui/badge";

type SupplierStatusBadgeProps = {
  isActive: boolean;
};

export function SupplierStatusBadge({
  isActive,
}: SupplierStatusBadgeProps) {
  return (
    <Badge variant={isActive ? "default" : "secondary"}>
      {isActive ? "Activo" : "Inactivo"}
    </Badge>
  );
}