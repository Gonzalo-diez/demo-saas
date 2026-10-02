"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import {
  addSupplierPaymentApi,
  deleteSupplierPaymentApi,
  editSupplierPaymentApi,
} from "@/features/admin/account-ledger/apis/account-ledger-api";
import type { LedgerPaymentCreateInput, LedgerPaymentUpdateInput } from "@/features/admin/account-ledger/types";

function invalidateSupplierLedger(queryClient: ReturnType<typeof useQueryClient>) {
  queryClient.invalidateQueries({ queryKey: ["supplier-purchases-ledger"] });
  queryClient.invalidateQueries({ queryKey: ["suppliers"] });
}

export function useAddSupplierPayment() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      purchaseInvoiceId,
      documentType,
      data,
    }: {
      purchaseInvoiceId: number;
      documentType: "purchase_invoice" | "purchase_quote";
      data: LedgerPaymentCreateInput;
    }) => addSupplierPaymentApi(purchaseInvoiceId, documentType, data),
    onSuccess: () => {
      invalidateSupplierLedger(queryClient);
      toast.success("Pago agregado");
    },
    onError: (error) => {
      toast.error(error instanceof Error ? error.message : "No se pudo agregar el pago");
    },
  });
}

export function useEditSupplierPayment() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      allocationId,
      data,
    }: {
      allocationId: number;
      data: LedgerPaymentUpdateInput;
    }) => editSupplierPaymentApi(allocationId, data),
    onSuccess: () => {
      invalidateSupplierLedger(queryClient);
      toast.success("Pago actualizado");
    },
    onError: (error) => {
      toast.error(error instanceof Error ? error.message : "No se pudo editar el pago");
    },
  });
}

export function useDeleteSupplierPayment() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (allocationId: number) => deleteSupplierPaymentApi(allocationId),
    onSuccess: () => {
      invalidateSupplierLedger(queryClient);
      toast.success("Pago eliminado");
    },
    onError: (error) => {
      toast.error(error instanceof Error ? error.message : "No se pudo eliminar el pago");
    },
  });
}