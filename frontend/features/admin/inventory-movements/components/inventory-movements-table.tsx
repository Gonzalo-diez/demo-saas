"use client";

import type { InventoryMovement } from "@/features/admin/inventory-movements/types";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";

type InventoryMovementsTableProps = {
  inventoryMovements: InventoryMovement[];
};

function formatMoney(value: string | null) {
  const numericValue = Number(value ?? 0);

  return new Intl.NumberFormat("es-AR", {
    style: "currency",
    currency: "ARS",
    maximumFractionDigits: 2,
  }).format(Number.isNaN(numericValue) ? 0 : numericValue);
}

function formatDate(value: string) {
  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return new Intl.DateTimeFormat("es-AR", {
    dateStyle: "short",
    timeStyle: "short",
  }).format(date);
}

function getMovementLabel(type: InventoryMovement["movement_type"]) {
  switch (type) {
    case "purchase":
      return "Compra";
    case "sale":
      return "Venta";
    case "adjustment_in":
      return "Ajuste entrada";
    case "adjustment_out":
      return "Ajuste salida";
    case "initial_stock":
      return "Stock inicial";
    default:
      return type;
  }
}

function getReferenceLabel(referenceType: InventoryMovement["reference_type"]) {
  switch (referenceType) {
    case "purchase_invoice":
      return "Remito compra";
    case "sales_invoice":
      return "Remito venta";
    case "order":
      return "Orden";
    case "draft":
      return "Borrador";
    case "manual_adjustment":
      return "Ajuste manual";
    case "import":
      return "Importación";
    default:
      return "-";
  }
}

function getMovementBadgeClass(type: InventoryMovement["movement_type"]) {
  switch (type) {
    case "purchase":
    case "adjustment_in":
    case "initial_stock":
      return "bg-brand-muted text-brand hover:bg-brand-muted";
    case "sale":
    case "adjustment_out":
      return "bg-destructive/15 text-destructive hover:bg-destructive/15";
    default:
      return "";
  }
}

export function InventoryMovementsTable({
  inventoryMovements,
}: InventoryMovementsTableProps) {
  if (inventoryMovements.length === 0) {
    return (
      <div className="rounded-2xl border bg-background p-8 text-center text-sm text-muted-foreground shadow-sm">
        No hay movimientos de inventario para mostrar.
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="grid gap-3 md:hidden">
        {inventoryMovements.map((movement) => (
          <div
            key={movement.id}
            className="rounded-2xl border bg-background p-4 shadow-sm"
          >
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0 space-y-1">
                <p className="truncate text-sm font-medium">
                  {movement.product?.name ?? `Producto #${movement.product_id}`}
                </p>
                <p className="text-xs text-muted-foreground">
                  {movement.product?.sku ?? "-"}
                </p>
                <p className="text-xs text-muted-foreground">
                  {formatDate(movement.created_at)}
                </p>
              </div>

              <Badge className={getMovementBadgeClass(movement.movement_type)}>
                {getMovementLabel(movement.movement_type)}
              </Badge>
            </div>

            <div className="mt-4 grid gap-3 rounded-xl border bg-muted/20 p-3 text-sm sm:grid-cols-2">
              <div>
                <p className="text-xs text-muted-foreground">Cantidad</p>
                <p className="font-medium">{movement.quantity}</p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Referencia</p>
                <p className="font-medium">
                  {getReferenceLabel(movement.reference_type)}
                  {movement.reference_id ? ` #${movement.reference_id}` : ""}
                </p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Stock antes</p>
                <p className="font-medium">{movement.stock_before}</p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Stock después</p>
                <p className="font-medium">{movement.stock_after}</p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Costo</p>
                <p className="font-medium">{formatMoney(movement.unit_cost)}</p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Precio</p>
                <p className="font-medium">{formatMoney(movement.unit_price)}</p>
              </div>
            </div>

            <div className="mt-3 text-sm">
              <p className="text-xs text-muted-foreground">Notas</p>
              <p className="mt-1 break-words">{movement.notes ?? "-"}</p>
            </div>
          </div>
        ))}
      </div>

      <div className="hidden overflow-hidden rounded-2xl border bg-background shadow-sm md:block">
        <div className="overflow-x-auto">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Fecha</TableHead>
                <TableHead>Producto</TableHead>
                <TableHead>Tipo</TableHead>
                <TableHead>Cantidad</TableHead>
                <TableHead>Stock antes</TableHead>
                <TableHead>Stock después</TableHead>
                <TableHead>Costo</TableHead>
                <TableHead>Precio</TableHead>
                <TableHead>Referencia</TableHead>
                <TableHead>Notas</TableHead>
              </TableRow>
            </TableHeader>

            <TableBody>
              {inventoryMovements.map((movement) => (
                <TableRow key={movement.id}>
                  <TableCell>{formatDate(movement.created_at)}</TableCell>
                  <TableCell className="min-w-[220px]">
                    <div className="space-y-1">
                      <p className="font-medium">
                        {movement.product?.name ?? `Producto #${movement.product_id}`}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        {movement.product?.sku ?? "-"}
                      </p>
                    </div>
                  </TableCell>
                  <TableCell>
                    <Badge className={getMovementBadgeClass(movement.movement_type)}>
                      {getMovementLabel(movement.movement_type)}
                    </Badge>
                  </TableCell>
                  <TableCell>{movement.quantity}</TableCell>
                  <TableCell>{movement.stock_before}</TableCell>
                  <TableCell>{movement.stock_after}</TableCell>
                  <TableCell>{formatMoney(movement.unit_cost)}</TableCell>
                  <TableCell>{formatMoney(movement.unit_price)}</TableCell>
                  <TableCell>
                    {getReferenceLabel(movement.reference_type)}
                    {movement.reference_id ? ` #${movement.reference_id}` : ""}
                  </TableCell>
                  <TableCell className="max-w-[260px] truncate">
                    {movement.notes ?? "-"}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      </div>
    </div>
  );
}