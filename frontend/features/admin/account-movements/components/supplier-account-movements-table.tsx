"use client";

import type { SupplierAccountMovement } from "@/features/admin/account-movements/types";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  AccountMovementTypeBadge,
  formatCurrency,
  formatDateTime,
  getPaymentMethodLabel,
} from "@/features/admin/account-movements/components/account-movement-helpers";

type SupplierAccountMovementsTableProps = {
  movements: SupplierAccountMovement[];
  showSupplier?: boolean;
};

export function SupplierAccountMovementsTable({
  movements,
  showSupplier = false,
}: SupplierAccountMovementsTableProps) {
  if (movements.length === 0) {
    return (
      <div className="rounded-2xl border bg-background p-8 text-center text-sm text-muted-foreground shadow-sm">
        No hay movimientos de cuenta corriente para mostrar.
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="grid gap-3 md:hidden">
        {movements.map((movement) => (
          <div
            key={movement.id}
            className="rounded-2xl border bg-background p-4 shadow-sm"
          >
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0 space-y-1">
                <p className="text-xs text-muted-foreground">
                  {formatDateTime(movement.created_at)}
                </p>
                {showSupplier && (
                  <p className="truncate text-sm font-semibold">
                    {movement.supplier?.name ?? `Proveedor #${movement.supplier_id}`}
                  </p>
                )}
                {movement.reference_summary ? (
                  <p className="truncate text-sm font-medium">
                    Remito {movement.reference_summary.invoice_number}
                  </p>
                ) : movement.payment_method ? (
                  <p className="truncate text-sm font-medium">
                    {getPaymentMethodLabel(movement.payment_method)}
                  </p>
                ) : null}
              </div>
              <AccountMovementTypeBadge type={movement.movement_type} />
            </div>

            <div className="mt-3 grid grid-cols-2 gap-3 rounded-xl border bg-muted/20 p-3 text-sm">
              <div>
                <p className="text-xs text-muted-foreground">Monto</p>
                <p
                  className={`font-medium ${Number(movement.amount) < 0 ? "text-brand" : "text-destructive"
                    }`}
                >
                  {formatCurrency(movement.amount)}
                </p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Saldo resultante</p>
                <p className="font-medium">
                  {formatCurrency(movement.balance_after)}
                </p>
              </div>
            </div>

            {movement.allocations.length > 0 && (
              <div className="mt-3 text-xs text-muted-foreground">
                Aplicado a:{" "}
                {movement.allocations
                  .map(
                    (a) =>
                      `${a.invoice_number ?? `#${a.invoice_id}`} (${formatCurrency(a.amount_applied)})`
                  )
                  .join(", ")}
              </div>
            )}

            {movement.notes && (
              <p className="mt-2 text-sm text-muted-foreground">
                {movement.notes}
              </p>
            )}
          </div>
        ))}
      </div>

      <div className="hidden overflow-hidden rounded-2xl border bg-background shadow-sm md:block">
        <div className="overflow-x-auto">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Fecha</TableHead>
                {showSupplier && <TableHead>Proveedor</TableHead>}
                <TableHead>Tipo</TableHead>
                <TableHead>Referencia</TableHead>
                <TableHead className="text-right">Monto</TableHead>
                <TableHead className="text-right">Saldo</TableHead>
                <TableHead>Método</TableHead>
                <TableHead>Notas</TableHead>
              </TableRow>
            </TableHeader>

            <TableBody>
              {movements.map((movement) => (
                <TableRow key={movement.id}>
                  <TableCell>{formatDateTime(movement.created_at)}</TableCell>
                  {showSupplier && (
                    <TableCell className="max-w-[180px] truncate font-medium">
                      {movement.supplier?.name ?? `Proveedor #${movement.supplier_id}`}
                    </TableCell>
                  )}
                  <TableCell>
                    <AccountMovementTypeBadge type={movement.movement_type} />
                  </TableCell>
                  <TableCell>
                    {movement.reference_summary ? (
                      <div className="space-y-1">
                        <p className="font-medium">
                          Remito {movement.reference_summary.invoice_number}
                        </p>
                        <p className="text-xs text-muted-foreground">
                          {formatCurrency(movement.reference_summary.total_amount)}
                        </p>
                      </div>
                    ) : movement.allocations.length > 0 ? (
                      <p className="text-xs text-muted-foreground">
                        {movement.allocations
                          .map(
                            (a) =>
                              `${a.invoice_number ?? `#${a.invoice_id}`} (${formatCurrency(a.amount_applied)})`
                          )
                          .join(", ")}
                      </p>
                    ) : (
                      <span className="text-sm text-muted-foreground">-</span>
                    )}
                  </TableCell>
                  <TableCell
                    className={`text-right font-medium ${Number(movement.amount) < 0 ? "text-brand" : "text-destructive"
                      }`}
                  >
                    {formatCurrency(movement.amount)}
                  </TableCell>
                  <TableCell className="text-right font-medium">
                    {formatCurrency(movement.balance_after)}
                  </TableCell>
                  <TableCell>
                    {getPaymentMethodLabel(movement.payment_method)}
                  </TableCell>
                  <TableCell className="max-w-[220px] truncate">
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