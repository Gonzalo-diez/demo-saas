"use client";

import { useState, Fragment } from "react";
import { ChevronLeft, ChevronRight, Wallet } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { useClientAccountMovements } from "@/features/admin/account-movements/hooks/use-client-account-movements";
import { ClientAccountMovementsTable } from "@/features/admin/account-movements/components/client-account-movements-table";
import { RegisterClientPaymentForm } from "@/features/admin/account-movements/components/register-client-payment-form";
import { formatCurrency } from "@/features/admin/account-movements/components/account-movement-helpers";
import type { Client } from "@/features/admin/clients/types";

type ClientAccountHistoryDialogProps = {
  client: Client;
};

const PAGE_SIZE = 20;

export function ClientAccountHistoryDialog({
  client,
}: ClientAccountHistoryDialogProps) {
  const [open, setOpen] = useState(false);
  const [page, setPage] = useState(1);

  const { data, isLoading, error, isFetching } = useClientAccountMovements(
    open ? client.id : null,
    page,
    PAGE_SIZE
  );

  const movements = data?.items ?? [];
  const total = data?.total ?? 0;
  const totalPages = data?.total_pages ?? 1;
  const currentPage = data?.page ?? 1;

  const balance = Number(client.current_balance ?? 0);

  return (
    <Dialog
      open={open}
      onOpenChange={(value) => {
        setOpen(value);
        if (!value) setPage(1);
      }}
    >
      <DialogTrigger asChild>
        <Button type="button" variant="outline" size="sm" className="w-full sm:w-auto">
          <Wallet className="mr-2 h-4 w-4" />
          Cuenta corriente
        </Button>
      </DialogTrigger>

      <DialogContent className="max-h-[90vh] overflow-y-auto px-4 sm:max-w-4xl sm:px-6">
        <DialogHeader>
          <DialogTitle>Cuenta corriente — {client.name}</DialogTitle>
          <DialogDescription>
            Historial de remitos y cobros. El saldo positivo indica que el
            cliente nos debe dinero.
          </DialogDescription>
        </DialogHeader>

        <div className="rounded-2xl border bg-muted/20 p-4">
          <p className="text-xs text-muted-foreground">Saldo actual</p>
          <p
            className={`text-2xl font-bold ${balance > 0 ? "text-destructive" : "text-brand"
              }`}
          >
            {formatCurrency(client.current_balance)}
          </p>
        </div>

        <div className="rounded-2xl border bg-card p-4 shadow-sm sm:p-5">
          <h4 className="mb-4 text-sm font-semibold">Registrar cobro</h4>
          <RegisterClientPaymentForm clientId={client.id} />
        </div>

        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h4 className="text-sm font-semibold">Historial de movimientos</h4>
            {isFetching && !isLoading && (
              <span className="text-xs text-muted-foreground">
                Actualizando...
              </span>
            )}
          </div>

          {error ? (
            <div className="rounded-2xl border border-destructive/30 bg-destructive/5 p-4 text-sm text-destructive">
              {error instanceof Error
                ? error.message
                : "No se pudo cargar la cuenta corriente."}
            </div>
          ) : isLoading && !data ? (
            <div className="rounded-2xl border bg-background p-6 text-sm text-muted-foreground shadow-sm">
              Cargando movimientos...
            </div>
          ) : (
            <Fragment>
              <ClientAccountMovementsTable movements={movements} />

              {totalPages > 1 && (
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">
                    Página {currentPage} de {totalPages} ({total} registros)
                  </span>
                  <div className="flex gap-2">
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      onClick={() => setPage((prev) => Math.max(1, prev - 1))}
                      disabled={currentPage === 1 || isLoading}
                    >
                      <ChevronLeft className="mr-1 h-4 w-4" />
                      Anterior
                    </Button>
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      onClick={() =>
                        setPage((prev) => Math.min(totalPages, prev + 1))
                      }
                      disabled={currentPage === totalPages || isLoading}
                    >
                      Siguiente
                      <ChevronRight className="ml-1 h-4 w-4" />
                    </Button>
                  </div>
                </div>
              )}
            </Fragment>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}