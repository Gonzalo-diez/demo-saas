import { Badge } from "@/components/ui/badge";

type ProductActiveBadgeProps = {
  isActive: boolean;
};

export function ProductActiveBadge({
  isActive,
}: ProductActiveBadgeProps) {
  return (
    <Badge variant={isActive ? "default" : "secondary"}>
      {isActive ? "Activo" : "Inactivo"}
    </Badge>
  );
}