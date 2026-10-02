"use client";

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import type { PurchaseInvoiceStatus } from "@/features/admin/purchase-invoices/types";

type PurchaseInvoiceFiltersProps = {
  status: PurchaseInvoiceStatus | "all";
  onStatusChange: (value: PurchaseInvoiceStatus | "all") => void;
};

export function PurchaseInvoiceFilters({
  status,
  onStatusChange,
}: PurchaseInvoiceFiltersProps) {
  return (
    <div className="grid gap-3 rounded-2xl border bg-background p-4 shadow-sm md:grid-cols-[260px]">
      <div className="space-y-1.5">
        <label className="text-sm font-medium">Estado</label>
        <Select
          value={status}
          onValueChange={(value) =>
            onStatusChange(value as PurchaseInvoiceStatus | "all")
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