import { Badge } from "@/components/ui/badge";

type SalesRepStatusBadgeProps = {
  isActive: boolean;
};

export function SalesRepStatusBadge({
  isActive,
}: SalesRepStatusBadgeProps) {
  return (
    <Badge variant={isActive ? "default" : "secondary"}>
      {isActive ? "Activo" : "Inactivo"}
    </Badge>
  );
}