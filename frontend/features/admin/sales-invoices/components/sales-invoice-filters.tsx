"use client";

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import type { SalesInvoiceStatus } from "@/features/admin/sales-invoices/types";

type SalesInvoiceFiltersProps = {
  status: SalesInvoiceStatus | "all";
  onStatusChange: (value: SalesInvoiceStatus | "all") => void;
};

export function SalesInvoiceFilters({
  status,
  onStatusChange,
}: SalesInvoiceFiltersProps) {
  return (
    <div className="grid gap-3 rounded-2xl border bg-background p-4 shadow-sm md:grid-cols-[260px]">
      <div className="space-y-1.5">
        <label className="text-sm font-medium">Estado</label>
        <Select
          value={status}
          onValueChange={(value) =>
            onStatusChange(value as SalesInvoiceStatus | "all")
          }
        >
          <SelectTrigger>
            <SelectValue placeholder="Filtrar por estado" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Todos</SelectItem>
            <SelectItem value="draft">Borrador</SelectItem>
            <SelectItem value="confirmed">Confirmada</SelectItem>
            <SelectItem value="cancelled">Cancelada</SelectItem>
          </SelectContent>
        </Select>
      </div>
    </div>
  );
}