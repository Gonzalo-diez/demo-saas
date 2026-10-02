"use client";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import {
  editOrderB2BApi,
  editOrderShopApi,
  updateOrderB2BApi,
} from "@/features/admin/orders/apis/orders-api";
import type {
  EditOrderB2BInput,
  EditOrderShopInput,
  UpdateOrderB2BInput,
} from "@/features/admin/orders/types";
import { toast } from "sonner";

// PUT /orders/b2b/{id}: a diferencia de useEditOrderB2B (que edita ítems,
// sucursal y referencia vía PATCH), esta mutation cambia el document_type
// (remito/presupuesto). El backend la rechaza con 400 si la orden ya generó
// su documento (invoice_generated).
export function useUpdateOrderB2B() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ orderId, data }: { orderId: number; data: UpdateOrderB2BInput }) =>
      updateOrderB2BApi(orderId, data),
    onSuccess: (_, { orderId }) => {
      queryClient.invalidateQueries({ queryKey: ["admin", "orders"] });
      queryClient.invalidateQueries({ queryKey: ["admin", "orders", orderId] });
    },
    onError: (error) => {
      toast.error(
        error instanceof Error ? error.message : "No se pudo cambiar el tipo de documento",
      );
    },
  });
}

export function useEditOrderB2B() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ orderId, data }: { orderId: number; data: EditOrderB2BInput }) =>
      editOrderB2BApi(orderId, data),
    onSuccess: (_, { orderId }) => {
      queryClient.invalidateQueries({ queryKey: ["admin", "orders"] });
      queryClient.invalidateQueries({ queryKey: ["admin", "orders", orderId] });
      queryClient.invalidateQueries({ queryKey: ["products"] });
      toast.success("Orden editada correctamente");
    },
    onError: (error) => {
      toast.error(
        error instanceof Error ? error.message : "Error al editar la orden",
      );
    },
  });
}

export function useEditOrderShop() {
  const queryClient = useQueryClient();
 
  return useMutation({
    mutationFn: ({ orderId, data }: { orderId: number; data: EditOrderShopInput }) =>
      editOrderShopApi(orderId, data),
    onSuccess: (_, { orderId }) => {
      queryClient.invalidateQueries({ queryKey: ["admin", "orders"] });
      queryClient.invalidateQueries({ queryKey: ["admin", "orders", orderId] });
      queryClient.invalidateQueries({ queryKey: ["products"] });
      toast.success("Orden editada correctamente");
    },
    onError: (error) => {
      toast.error(
        error instanceof Error ? error.message : "Error al editar la orden",
      );
    },
  });
}