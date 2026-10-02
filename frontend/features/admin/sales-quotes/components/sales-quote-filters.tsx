"use client";

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import type { SalesQuoteStatus } from "@/features/admin/sales-quotes/types";

type SalesQuoteFiltersProps = {
  status: SalesQuoteStatus | "all";
  onStatusChange: (value: SalesQuoteStatus | "all") => void;
};

export function SalesQuoteFilters({ status, onStatusChange }: SalesQuoteFiltersProps) {
  return (
    <div className="grid gap-3 rounded-2xl border bg-background p-4 shadow-sm md:grid-cols-[260px]">
      <div className="space-y-1.5">
        <label className="text-sm font-medium">Estado</label>
        <Select
          value={status}
          onValueChange={(value) => onStatusChange(value as SalesQuoteStatus | "all")}
        >
          <SelectTrigger>
            <SelectValue placeholder="Filtrar por estado" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Todos</SelectItem>
            <SelectItem value="draft">Borrador</SelectItem>
            <SelectItem value="sent">Enviado</SelectItem>
            <SelectItem value="approved">Aprobado</SelectItem>
            <SelectItem value="rejected">Rechazado</SelectItem>
            <SelectItem value="expired">Expirado</SelectItem>
            <SelectItem value="cancelled">Cancelado</SelectItem>
          </SelectContent>
        </Select>
      </div>
    </div>
  );
}
