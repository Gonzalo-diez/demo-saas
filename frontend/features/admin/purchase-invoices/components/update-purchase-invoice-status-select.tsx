"use client";

import { toast } from "sonner";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useUpdatePurchaseInvoiceStatus } from "@/features/admin/purchase-invoices/hooks/use-update-purchase-invoice-status";
import type {
  PurchaseInvoice,
  PurchaseInvoiceStatus,
} from "@/features/admin/purchase-invoices/types";

type UpdatePurchaseInvoiceStatusSelectProps = {
  purchaseInvoice: PurchaseInvoice;
};

export function UpdatePurchaseInvoiceStatusSelect({
  purchaseInvoice,
}: UpdatePurchaseInvoiceStatusSelectProps) {
  const updateStatus = useUpdatePurchaseInvoiceStatus();

  async function handleChange(value: string) {
    try {
      await updateStatus.mutateAsync({
        purchaseInvoiceId: purchaseInvoice.id,
        status: value as PurchaseInvoiceStatus,
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
      value={purchaseInvoice.status}
      onValueChange={handleChange}
      disabled={updateStatus.isPending}
    >
      <SelectTrigger className="w-[160px]">
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