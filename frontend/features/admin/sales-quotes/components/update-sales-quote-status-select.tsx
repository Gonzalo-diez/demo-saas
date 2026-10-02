"use client";

import { toast } from "sonner";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useUpdateSalesQuoteStatus } from "@/features/admin/sales-quotes/hooks/use-update-sales-quote-status";
import { SalesQuoteStatusBadge } from "@/features/admin/sales-quotes/components/sales-quote-status-badge";
import type { SalesQuote, SalesQuoteStatus } from "@/features/admin/sales-quotes/types";

type UpdateSalesQuoteStatusSelectProps = {
  salesQuote: SalesQuote;
};

export function UpdateSalesQuoteStatusSelect({
  salesQuote,
}: UpdateSalesQuoteStatusSelectProps) {
  const updateStatus = useUpdateSalesQuoteStatus();

  // Un presupuesto que nació de un pedido tiene su ciclo de vida gobernado
  // por el pedido (el backend devuelve 400 ante cualquier cambio manual).
  const isLockedByOrder = salesQuote.order_id !== null;

  async function handleChange(value: string) {
    try {
      await updateStatus.mutateAsync({
        salesQuoteId: salesQuote.id,
        status: value as SalesQuoteStatus,
      });

      toast.success("Estado actualizado", {
        position: "top-right",
        duration: 4000,
      });
    } catch (error) {
      toast.error(
        error instanceof Error ? error.message : "No se pudo actualizar el estado",
        { position: "top-right", duration: 4000 }
      );
    }
  }

  if (isLockedByOrder) {
    return (
      <div
        className="w-full md:w-[160px]"
        title={`Nació del pedido #${salesQuote.order_id}: su estado se gestiona desde el pedido.`}
      >
        <SalesQuoteStatusBadge status={salesQuote.status} />
      </div>
    );
  }

  return (
    <Select
      value={salesQuote.status}
      onValueChange={handleChange}
      disabled={updateStatus.isPending}
    >
      <SelectTrigger className="w-full md:w-[160px]">
        <SelectValue />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value="draft">Borrador</SelectItem>
        <SelectItem value="sent">Enviado</SelectItem>
        <SelectItem value="approved">Aprobado</SelectItem>
        <SelectItem value="rejected">Rechazado</SelectItem>
        <SelectItem value="expired">Expirado</SelectItem>
        <SelectItem value="cancelled">Cancelado</SelectItem>
      </SelectContent>
    </Select>
  );
}