"use client";

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import type { CheckDirection, CheckStatus } from "@/features/admin/checks/types";

type ChecksFiltersProps = {
  direction: CheckDirection | "all";
  status: CheckStatus | "all";
  onDirectionChange: (value: CheckDirection | "all") => void;
  onStatusChange: (value: CheckStatus | "all") => void;
};

export function ChecksFilters({
  direction,
  status,
  onDirectionChange,
  onStatusChange,
}: ChecksFiltersProps) {
  return (
    <div className="grid gap-3 rounded-2xl border bg-background p-4 shadow-sm sm:grid-cols-2 md:grid-cols-[220px_220px]">
      <div className="space-y-1.5">
        <label className="text-sm font-medium">Dirección</label>
        <Select
          value={direction}
          onValueChange={(value) => onDirectionChange(value as CheckDirection | "all")}
        >
          <SelectTrigger>
            <SelectValue placeholder="Todas" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Todas</SelectItem>
            <SelectItem value="received">Recibidos (de clientes)</SelectItem>
            <SelectItem value="issued">Emitidos (a proveedores)</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <div className="space-y-1.5">
        <label className="text-sm font-medium">Estado</label>
        <Select
          value={status}
          onValueChange={(value) => onStatusChange(value as CheckStatus | "all")}
        >
          <SelectTrigger>
            <SelectValue placeholder="Todos" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Todos</SelectItem>
            <SelectItem value="pendiente">Pendiente</SelectItem>
            <SelectItem value="depositado">Depositado</SelectItem>
            <SelectItem value="acreditado">Acreditado</SelectItem>
            <SelectItem value="rechazado">Rechazado</SelectItem>
          </SelectContent>
        </Select>
      </div>
    </div>
  );
}
