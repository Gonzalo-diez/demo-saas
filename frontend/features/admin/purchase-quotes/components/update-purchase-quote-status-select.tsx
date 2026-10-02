"use client";

import { toast } from "sonner";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useUpdatePurchaseQuoteStatus } from "@/features/admin/purchase-quotes/hooks/use-update-purchase-quote-status";
import type {
  PurchaseQuote,
  PurchaseQuoteStatus,
} from "@/features/admin/purchase-quotes/types";

type UpdatePurchaseQuoteStatusSelectProps = {
  purchaseQuote: PurchaseQuote;
};

export function UpdatePurchaseQuoteStatusSelect({
  purchaseQuote,
}: UpdatePurchaseQuoteStatusSelectProps) {
  const updateStatus = useUpdatePurchaseQuoteStatus();

  async function handleChange(value: string) {
    try {
      await updateStatus.mutateAsync({
        purchaseQuoteId: purchaseQuote.id,
        status: value as PurchaseQuoteStatus,
      });

      toast.success("Estado actualizado", { position: "top-right", duration: 4000 });
    } catch (error) {
      toast.error(
        error instanceof Error ? error.message : "No se pudo actualizar el estado",
        { position: "top-right", duration: 4000 }
      );
    }
  }

  return (
    <Select
      value={purchaseQuote.status}
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
      </SelectContent>
    </Select>
  );
}
