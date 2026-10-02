"use client";

import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

type ClientFiltersProps = {
  search: string;
  status: "" | "active" | "inactive";
  sort: "" | "name" | "created_at";
  onSearchChange: (value: string) => void;
  onStatusChange: (value: "" | "active" | "inactive") => void;
  onSortChange: (value: "" | "name" | "created_at") => void;
};

export function ClientFilters({
  search,
  status,
  sort,
  onSearchChange,
  onStatusChange,
  onSortChange,
}: ClientFiltersProps) {
  return (
    <div className="flex flex-col gap-3 md:flex-row md:items-center">
      <Input
        placeholder="Buscar clientes..."
        value={search}
        onChange={(e) => onSearchChange(e.target.value)}
        className="md:max-w-sm"
      />

      <Select
        value={status || "all"}
        onValueChange={(value) =>
          onStatusChange(value === "all" ? "" : (value as "active" | "inactive"))
        }
      >
        <SelectTrigger className="w-full md:w-[180px]">
          <SelectValue placeholder="Estado" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">Todos</SelectItem>
          <SelectItem value="active">Activos</SelectItem>
          <SelectItem value="inactive">Inactivos</SelectItem>
        </SelectContent>
      </Select>

      <Select
        value={sort || "created_at"}
        onValueChange={(value) =>
          onSortChange(value === "none" ? "" : (value as "name" | "created_at"))
        }
      >
        <SelectTrigger className="w-full md:w-[180px]">
          <SelectValue placeholder="Ordenar por" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="created_at">Más recientes</SelectItem>
          <SelectItem value="name">Nombre</SelectItem>
        </SelectContent>
      </Select>
    </div>
  );
}