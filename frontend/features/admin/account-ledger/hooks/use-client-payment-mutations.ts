"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import {
  addClientPaymentApi,
  deleteClientPaymentApi,
  editClientPaymentApi,
} from "@/features/admin/account-ledger/apis/account-ledger-api";
import type { LedgerPaymentCreateInput, LedgerPaymentUpdateInput } from "@/features/admin/account-ledger/types";

function invalidateClientLedger(queryClient: ReturnType<typeof useQueryClient>) {
  queryClient.invalidateQueries({ queryKey: ["client-sales-ledger"] });
  queryClient.invalidateQueries({ queryKey: ["clients"] });
}

export function useAddClientPayment() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      salesInvoiceId,
      documentType,
      data,
    }: {
      salesInvoiceId: number;
      documentType: "sales_invoice" | "sales_quote";
      data: LedgerPaymentCreateInput;
    }) => addClientPaymentApi(salesInvoiceId, documentType, data),
    onSuccess: () => {
      invalidateClientLedger(queryClient);
      toast.success("Pago agregado");
    },
    onError: (error) => {
      toast.error(error instanceof Error ? error.message : "No se pudo agregar el pago");
    },
  });
}

export function useEditClientPayment() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      allocationId,
      data,
    }: {
      allocationId: number;
      data: LedgerPaymentUpdateInput;
    }) => editClientPaymentApi(allocationId, data),
    onSuccess: () => {
      invalidateClientLedger(queryClient);
      toast.success("Pago actualizado");
    },
    onError: (error) => {
      toast.error(error instanceof Error ? error.message : "No se pudo editar el pago");
    },
  });
}

export function useDeleteClientPayment() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (allocationId: number) => deleteClientPaymentApi(allocationId),
    onSuccess: () => {
      invalidateClientLedger(queryClient);
      toast.success("Pago eliminado");
    },
    onError: (error) => {
      toast.error(error instanceof Error ? error.message : "No se pudo eliminar el pago");
    },
  });
}