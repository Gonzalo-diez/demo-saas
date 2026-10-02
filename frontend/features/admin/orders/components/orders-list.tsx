"use client";

import { useState } from "react";
import { ClipboardList } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useAdminOrders } from "@/features/admin/orders/hooks/use-orders";
import { OrdersTable } from "@/features/admin/orders/components/orders-table";
import type { OrderStatus } from "@/features/admin/orders/types";

const PAGE_SIZE = 20;

export function OrdersList() {
  const [page, setPage] = useState(1);
  const [status, setStatus] = useState<OrderStatus | "all">("all");

  const { data, isLoading, error, isFetching } = useAdminOrders({
    page,
    page_size: PAGE_SIZE,
    status: status === "all" ? undefined : status,
  });

  function handleStatusChange(value: OrderStatus | "all") {
    setStatus(value);
    setPage(1);
  }

  const orders = data?.items ?? [];
  const total = data?.total ?? 0;
  const currentPage = data?.page ?? 1;
  const pageSize = data?.page_size ?? PAGE_SIZE;
  const totalPages = Math.ceil(total / pageSize);

  const startItem = total === 0 ? 0 : (currentPage - 1) * pageSize + 1;
  const endItem = Math.min(currentPage * pageSize, total);

  return (
    <div className="w-full max-w-full space-y-4 min-w-0">
      {/* Barra superior de controles */}
      <div className="flex flex-col gap-4 rounded-2xl border bg-background p-4 shadow-sm xl:flex-row xl:items-center xl:justify-between">
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <ClipboardList className="h-4 w-4 shrink-0" />
          <div>
            <p>
              Mostrando {startItem}-{endItem} de {total} órdenes
            </p>
            {isFetching && !isLoading ? (
              <p className="text-xs text-muted-foreground/80">Actualizando...</p>
            ) : null}
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-3 sm:flex-nowrap">
          <Select
            value={status}
            onValueChange={(value) => 
              handleStatusChange(value as OrderStatus | "all")
            }
          >
            <SelectTrigger className="w-full sm:w-[180px]">
              <SelectValue placeholder="Filtrar estado" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Todos los estados</SelectItem>
              <SelectItem value="pending_confirmation">Pendiente</SelectItem>
              <SelectItem value="confirmed">Confirmado</SelectItem>
              <SelectItem value="preparing">Preparando</SelectItem>
              <SelectItem value="shipped">Enviado</SelectItem>
              <SelectItem value="delivered">Entregado</SelectItem>
              <SelectItem value="cancelled">Cancelado</SelectItem>
            </SelectContent>
          </Select>

          <span className="whitespace-nowrap text-sm text-muted-foreground">
            Página {currentPage} de {totalPages || 1}
          </span>

          <div className="flex w-full items-center gap-2 sm:w-auto">
            <Button
              type="button"
              variant="outline"
              size="sm"
              className="flex-1 sm:flex-none"
              onClick={() => setPage((prev) => Math.max(1, prev - 1))}
              disabled={currentPage === 1 || isLoading}
            >
              Anterior
            </Button>

            <Button
              type="button"
              variant="outline"
              size="sm"
              className="flex-1 sm:flex-none"
              onClick={() => setPage((prev) => Math.min(totalPages, prev + 1))}
              disabled={currentPage >= totalPages || isLoading}
            >
              Siguiente
            </Button>
          </div>
        </div>
      </div>

      {/* Contenedor con scroll aislado para la tabla */}
      {error ? (
        <div className="rounded-2xl border border-destructive/20 bg-destructive/10 p-6 text-sm text-destructive shadow-sm">
          {error instanceof Error ? error.message : "No se pudieron cargar las órdenes"}
        </div>
      ) : isLoading && !data ? (
        <div className="rounded-2xl border bg-background p-6 text-sm text-muted-foreground shadow-sm">
          Cargando órdenes...
        </div>
      ) : (
        <div className="w-full max-w-full overflow-hidden rounded-2xl border bg-background shadow-sm">
          <div className="overflow-x-auto">
            <OrdersTable orders={orders} />
          </div>
        </div>
      )}
    </div>
  );
}