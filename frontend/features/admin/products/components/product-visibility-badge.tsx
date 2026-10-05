import { Badge } from "@/components/ui/badge";

export function ProductVisibilityBadge({ isPublic }: { isPublic: boolean }) {
  return (
    <Badge variant={isPublic ? "default" : "secondary"}>
      {isPublic ? "En catálogo" : "Oculto"}
    </Badge>
  );
}
