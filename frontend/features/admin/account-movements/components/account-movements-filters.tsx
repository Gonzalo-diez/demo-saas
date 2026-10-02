"use client";

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import type {
  AccountMovementType,
  AccountReferenceType,
} from "@/features/admin/account-movements/types";

type AccountMovementsFiltersProps = {
  movementType: AccountMovementType | "all";
  referenceType: AccountReferenceType | "all";
  onMovementTypeChange: (value: AccountMovementType | "all") => void;
  onReferenceTypeChange: (value: AccountReferenceType | "all") => void;
};

export function AccountMovementsFilters({
  movementType,
  referenceType,
  onMovementTypeChange,
  onReferenceTypeChange,
}: AccountMovementsFiltersProps) {
  return (
    <div className="grid gap-3 rounded-2xl border bg-background p-4 shadow-sm md:grid-cols-2">
      <div className="space-y-1.5">
        <label className="text-sm font-medium">Tipo de movimiento</label>
        <Select
          value={movementType}
          onValueChange={(value) =>
            onMovementTypeChange(value as AccountMovementType | "all")
          }
        >
          <SelectTrigger>
            <SelectValue placeholder="Filtrar por movimiento" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Todos</SelectItem>
            <SelectItem value="invoice">Remito</SelectItem>
            <SelectItem value="invoice_reversal">Reversión del remito</SelectItem>
            <SelectItem value="payment">Cobro/Pago</SelectItem>
            <SelectItem value="credit_note">Nota de crédito</SelectItem>
            <SelectItem value="adjustment">Ajuste manual</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <div className="space-y-1.5">
        <label className="text-sm font-medium">Referencia</label>
        <Select
          value={referenceType}
          onValueChange={(value) =>
            onReferenceTypeChange(value as AccountReferenceType | "all")
          }
        >
          <SelectTrigger>
            <SelectValue placeholder="Filtrar por referencia" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Todas</SelectItem>
            <SelectItem value="sales_invoice">Remito de venta</SelectItem>
            <SelectItem value="purchase_invoice">Remito de compra</SelectItem>
            <SelectItem value="payment">Pago</SelectItem>
            <SelectItem value="manual_adjustment">Ajuste manual</SelectItem>
          </SelectContent>
        </Select>
      </div>
    </div>
  );
}
