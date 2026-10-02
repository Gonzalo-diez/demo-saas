"use client";

import { useState } from "react";
import { SlidersHorizontal } from "lucide-react";

import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";

import { CatalogFilters } from "@/features/shop/products/filters/catalog-filters";

type Props = {
  brands: string[];
  currentFilters: {
    search?: string;
    brand?: string;
    sort?: string;
  };
  salesRepId?: number;
};

export function MobileFilters({
  brands,
  currentFilters,
  salesRepId,
}: Props) {
  const [open, setOpen] = useState(false);

  return (
    <Sheet open={open} onOpenChange={setOpen}>
      <SheetTrigger asChild>
        <button
          className="flex items-center gap-2 rounded-lg border px-4 py-2 text-sm font-medium transition-colors hover:bg-muted"
        >
          <SlidersHorizontal size={16} />
          Filtros
        </button>
      </SheetTrigger>

      <SheetContent side="left" className="w-[300px] sm:w-[340px]">
        <SheetHeader>
          <SheetTitle>Filtros</SheetTitle>
        </SheetHeader>

        <div className="mt-6">
          <CatalogFilters
            brands={brands}
            currentFilters={currentFilters}
            salesRepId={salesRepId}
            onFilterChange={() => setOpen(false)}
          />
        </div>
      </SheetContent>
    </Sheet>
  );
}