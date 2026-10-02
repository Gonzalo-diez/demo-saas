"use client";

import { toast } from "sonner";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useUpdateSalesInvoiceStatus } from "@/features/admin/sales-invoices/hooks/use-update-sales-invoice-status";
import type {
  SalesInvoice,
  SalesInvoiceStatus,
} from "@/features/admin/sales-invoices/types";

type UpdateSalesInvoiceStatusSelectProps = {
  salesInvoice: SalesInvoice;
};

export function UpdateSalesInvoiceStatusSelect({
  salesInvoice,
}: UpdateSalesInvoiceStatusSelectProps) {
  const updateStatus = useUpdateSalesInvoiceStatus();

  async function handleChange(value: string) {
    try {
      await updateStatus.mutateAsync({
        salesInvoiceId: salesInvoice.id,
        status: value as SalesInvoiceStatus,
      });

      toast.success("Estado actualizado", {
        position: "top-right",
        duration: 4000,
      });
    } catch (error) {
      toast.error(
        error instanceof Error
          ? error.message
          : "No se pudo actualizar el estado",
        {
          position: "top-right",
          duration: 4000,
        }
      );
    }
  }

  return (
    <Select
      value={salesInvoice.status}
      onValueChange={handleChange}
      disabled={updateStatus.isPending}
    >
      <SelectTrigger className="w-full md:w-[160px]">
        <SelectValue />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value="draft">Borrador</SelectItem>
        <SelectItem value="confirmed">Confirmada</SelectItem>
        <SelectItem value="cancelled">Cancelada</SelectItem>
      </SelectContent>
    </Select>
  );
}