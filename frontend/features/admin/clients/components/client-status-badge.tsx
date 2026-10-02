import { Badge } from "@/components/ui/badge";

type ClientStatusBadgeProps = {
  isActive: boolean;
};

export function ClientStatusBadge({ isActive }: ClientStatusBadgeProps) {
  return (
    <Badge variant={isActive ? "default" : "secondary"}>
      {isActive ? "Activo" : "Inactivo"}
    </Badge>
  );
}