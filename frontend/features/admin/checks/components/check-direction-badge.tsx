import { ArrowDownLeft, ArrowUpRight } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import type { CheckDirection } from "@/features/admin/checks/types";

type CheckDirectionBadgeProps = {
  direction: CheckDirection;
};

export function CheckDirectionBadge({ direction }: CheckDirectionBadgeProps) {
  if (direction === "received") {
    return (
      <Badge variant="outline" className="gap-1 border-emerald-300 text-emerald-700">
        <ArrowDownLeft className="h-3 w-3" />
        Recibido
      </Badge>
    );
  }

  return (
    <Badge variant="outline" className="gap-1 border-amber-300 text-amber-700">
      <ArrowUpRight className="h-3 w-3" />
      Emitido
    </Badge>
  );
}
