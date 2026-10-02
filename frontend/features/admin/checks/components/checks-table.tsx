"use client";

import type { Check } from "@/features/admin/checks/types";
import { CheckActions } from "@/features/admin/checks/components/check-actions";
import { CheckDirectionBadge } from "@/features/admin/checks/components/check-direction-badge";
import { CheckStatusBadge } from "@/features/admin/checks/components/check-status-badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

type ChecksTableProps = {
  checks: Check[];
  clientNameById: Record<number, string>;
  supplierNameById: Record<number, string>;
};

function formatMoney(value: string) {
  const numericValue = Number(value ?? 0);
  return new Intl.NumberFormat("es-AR", {
    style: "currency",
    currency: "ARS",
    maximumFractionDigits: 2,
  }).format(Number.isNaN(numericValue) ? 0 : numericValue);
}

function formatDate(value: string | null) {
  if (!value) return "-";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat("es-AR").format(date);
}

function getCounterpartyName(
  check: Check,
  clientNameById: Record<number, string>,
  supplierNameById: Record<number, string>
) {
  if (check.direction === "received" && check.client_id) {
    return clientNameById[check.client_id] ?? `Cliente #${check.client_id}`;
  }
  if (check.direction === "issued" && check.supplier_id) {
    return supplierNameById[check.supplier_id] ?? `Proveedor #${check.supplier_id}`;
  }
  return "-";
}

export function ChecksTable({ checks, clientNameById, supplierNameById }: ChecksTableProps) {
  if (checks.length === 0) {
    return (
      <div className="rounded-2xl border bg-background p-8 text-center text-sm text-muted-foreground shadow-sm">
        No hay cheques para mostrar.
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Cards para Mobile */}
      <div className="grid gap-3 md:hidden">
        {checks.map((check) => (
          <div key={check.id} className="rounded-2xl border bg-background p-4 shadow-sm space-y-3">
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0 space-y-0.5">
                <p className="text-sm font-bold font-mono">#{check.check_number}</p>
                <p className="truncate text-sm font-semibold text-foreground">
                  {getCounterpartyName(check, clientNameById, supplierNameById)}
                </p>
              </div>
              <div className="flex flex-col items-end gap-1.5">
                <CheckDirectionBadge direction={check.direction} />
                <CheckStatusBadge status={check.status} />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-2 rounded-xl border bg-muted/20 p-2.5 text-xs">
              <div>
                <p className="text-muted-foreground">Vencimiento</p>
                <p className="font-medium">{formatDate(check.due_date)}</p>
              </div>
              <div>
                <p className="text-muted-foreground text-right">Monto</p>
                <p className="font-bold text-right text-foreground">{formatMoney(check.amount)}</p>
              </div>
            </div>

            <div className="pt-1">
              <CheckActions check={check} />
            </div>
          </div>
        ))}
      </div>

      {/* Tabla para Desktop */}
      <div className="hidden overflow-hidden rounded-2xl border bg-background shadow-sm md:block">
        <div className="overflow-x-auto">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-[60px]">ID</TableHead>
                <TableHead>Dirección</TableHead>
                <TableHead>Nº cheque</TableHead>
                <TableHead>Cliente / Proveedor</TableHead>
                <TableHead>Banco</TableHead>
                <TableHead>Emisión</TableHead>
                <TableHead>Pago</TableHead>
                <TableHead>Vencimiento</TableHead>
                <TableHead className="text-right">Monto</TableHead>
                <TableHead>Estado</TableHead>
                <TableHead className="text-right">Acciones</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {checks.map((check) => (
                <TableRow key={check.id}>
                  <TableCell className="font-medium">#{check.id}</TableCell>
                  <TableCell>
                    <CheckDirectionBadge direction={check.direction} />
                  </TableCell>
                  <TableCell className="font-mono text-sm">{check.check_number}</TableCell>
                  <TableCell className="min-w-[160px] max-w-[200px] truncate font-semibold">
                    {getCounterpartyName(check, clientNameById, supplierNameById)}
                  </TableCell>
                  <TableCell className="text-sm text-muted-foreground">
                    {check.bank_name ?? "-"}
                  </TableCell>
                  <TableCell>{formatDate(check.issue_date)}</TableCell>
                  <TableCell>{formatDate(check.payment_date)}</TableCell>
                  <TableCell>{formatDate(check.due_date)}</TableCell>
                  <TableCell className="text-right font-medium">
                    {formatMoney(check.amount)}
                  </TableCell>
                  <TableCell>
                    <CheckStatusBadge status={check.status} />
                  </TableCell>
                  <TableCell>
                    <CheckActions check={check} />
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
