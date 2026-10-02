"use client";

import { useMemo } from "react";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import type {
  InventoryMovementType,
  InventoryReferenceType,
} from "@/features/admin/inventory-movements/types";
import { useProducts } from "@/features/admin/products/hooks/use-products";

type InventoryMovementFiltersProps = {
  productId: number | null;
  movementType: InventoryMovementType | "all";
  referenceType: InventoryReferenceType | "all";
  onProductIdChange: (value: number | null) => void;
  onMovementTypeChange: (value: InventoryMovementType | "all") => void;
  onReferenceTypeChange: (value: InventoryReferenceType | "all") => void;
};

export function InventoryMovementFilters({
  productId,
  movementType,
  referenceType,
  onProductIdChange,
  onMovementTypeChange,
  onReferenceTypeChange,
}: InventoryMovementFiltersProps) {
  const productsQuery = useProducts({
    page: 1,
    page_size: 20,
    search: "",
    status: "active",
    brand: "",
    sort: "name-asc",
  });

  const products = useMemo(() => productsQuery.data?.items ?? [], [productsQuery.data]);

  return (
    <div className="grid gap-3 rounded-2xl border bg-background p-4 shadow-sm md:grid-cols-3">
      <div className="space-y-1.5">
        <label className="text-sm font-medium">Producto</label>
        <Select
          value={productId ? String(productId) : "__empty__"}
          onValueChange={(value) =>
            onProductIdChange(value === "__empty__" ? null : Number(value))
          }
        >
          <SelectTrigger>
            <SelectValue placeholder="Filtrar por producto" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="__empty__">Todos</SelectItem>
            {products.map((product) => (
              <SelectItem key={product.id} value={String(product.id)}>
                {product.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div className="space-y-1.5">
        <label className="text-sm font-medium">Tipo de movimiento</label>
        <Select
          value={movementType}
          onValueChange={(value) =>
            onMovementTypeChange(value as InventoryMovementType | "all")
          }
        >
          <SelectTrigger>
            <SelectValue placeholder="Filtrar por movimiento" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Todos</SelectItem>
            <SelectItem value="purchase">Compra</SelectItem>
            <SelectItem value="sale">Venta</SelectItem>
            <SelectItem value="adjustment_in">Ajuste entrada</SelectItem>
            <SelectItem value="adjustment_out">Ajuste salida</SelectItem>
            <SelectItem value="initial_stock">Stock inicial</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <div className="space-y-1.5">
        <label className="text-sm font-medium">Referencia</label>
        <Select
          value={referenceType}
          onValueChange={(value) =>
            onReferenceTypeChange(value as InventoryReferenceType | "all")
          }
        >
          <SelectTrigger>
            <SelectValue placeholder="Filtrar por referencia" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Todas</SelectItem>
            <SelectItem value="purchase_invoice">Remito compra</SelectItem>
            <SelectItem value="sales_invoice">Remito venta</SelectItem>
            <SelectItem value="order">Orden</SelectItem>
            <SelectItem value="manual_adjustment">Ajuste manual</SelectItem>
            <SelectItem value="import">Importación</SelectItem>
          </SelectContent>
        </Select>
      </div>
    </div>
  );
}