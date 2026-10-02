"use client";

import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import type {
  SalesRepSort,
  SalesRepStatusFilter,
} from "@/features/admin/sales-reps/types";

type SalesRepFiltersProps = {
  search: string;
  status: SalesRepStatusFilter;
  sort: SalesRepSort;
  onSearchChange: (value: string) => void;
  onStatusChange: (value: SalesRepStatusFilter) => void;
  onSortChange: (value: SalesRepSort) => void;
};

export function SalesRepFilters({
  search,
  status,
  sort,
  onSearchChange,
  onStatusChange,
  onSortChange,
}: SalesRepFiltersProps) {
  return (
    <div className="grid gap-3 rounded-2xl border bg-background p-4 shadow-sm md:grid-cols-3">
      <Input
        value={search}
        onChange={(event) => onSearchChange(event.target.value)}
        placeholder="Buscar por nombre o email"
      />

      <Select
        value={status || "all"}
        onValueChange={(value) =>
          onStatusChange(value === "all" ? "" : (value as SalesRepStatusFilter))
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

      <Select
        value={sort || "default"}
        onValueChange={(value) =>
          onSortChange(value === "default" ? "" : (value as SalesRepSort))
        }
      >
        <SelectTrigger>
          <SelectValue placeholder="Ordenar por" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="default">Por defecto</SelectItem>
          <SelectItem value="name">Nombre</SelectItem>
          <SelectItem value="created_at">Más recientes</SelectItem>
        </SelectContent>
      </Select>
    </div>
  );
}