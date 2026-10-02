"use client";

import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import type { SupplierStatusFilter } from "@/features/admin/suppliers/types";

type SupplierFiltersProps = {
  search: string;
  status: SupplierStatusFilter;
  onSearchChange: (value: string) => void;
  onStatusChange: (value: SupplierStatusFilter) => void;
};

export function SupplierFilters({
  search,
  status,
  onSearchChange,
  onStatusChange,
}: SupplierFiltersProps) {
  return (
    <div className="grid gap-3 rounded-2xl border bg-background p-4 shadow-sm md:grid-cols-2">
      <Input
        value={search}
        onChange={(event) => onSearchChange(event.target.value)}
        placeholder="Buscar por nombre"
      />

      <Select
        value={status || "all"}
        onValueChange={(value) =>
          onStatusChange(value === "all" ? "" : (value as SupplierStatusFilter))
        }
      >
        <SelectTrigger>
          <SelectValue placeholder="Estado" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">Todos</SelectItem>
          <SelectItem value="active">Activos</SelectItem>
          <SelectItem value="inactive">Inactivos</SelectItem>
        </SelectContent>
      </Select>
    </div>
  );
}