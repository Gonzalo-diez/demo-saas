"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { setProductPublicApi } from "@/features/admin/products/apis/products-api";

export function useToggleProductVisibility() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ productId, isPublic }: { productId: number; isPublic: boolean }) =>
      setProductPublicApi(productId, isPublic),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: ["products"] });
      queryClient.invalidateQueries({ queryKey: ["shop-products"] });
      toast.success(
        variables.isPublic ? "Producto publicado en el catálogo" : "Producto oculto del catálogo",
      );
    },
    onError: (error) =>
      toast.error(error instanceof Error ? error.message : "No se pudo cambiar la visibilidad"),
  });
}
