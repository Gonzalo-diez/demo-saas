"use client";

import { Search } from "lucide-react";

type SearchFilterProps = {
  value: string;
  onChange: (value: string) => void;
};

export function SearchFilter({ value, onChange }: SearchFilterProps) {
  return (
    <div className="flex flex-col gap-1.5">
      <label htmlFor="search" className="text-sm font-medium">
        Buscar
      </label>
      <div className="relative">
        <Search className="absolute left-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground pointer-events-none" />
        <input
          id="search"
          type="text"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder="Buscar producto..."
          className="w-full rounded-lg border border-input bg-background py-2 pl-8 pr-3 text-sm outline-none transition-colors placeholder:text-muted-foreground focus:ring-2 focus:ring-ring/50"
        />
      </div>
    </div>
  );
}