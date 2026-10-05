"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import {
  createCategoryApi,
  deleteCategoryApi,
  setCategoryPublicApi,
  updateCategoryApi,
} from "@/features/admin/categories/apis/categories-api";
import { CATEGORIES_QUERY_KEY } from "@/features/admin/categories/hooks/use-categories";
import type { UpdateCategoryInput } from "@/features/admin/categories/types";

function useRefreshCategories() {
  const queryClient = useQueryClient();
  return () => {
    queryClient.invalidateQueries({ queryKey: CATEGORIES_QUERY_KEY });
    // el catálogo de la tienda y los productos dependen de las categorías
    queryClient.invalidateQueries({ queryKey: ["shop-categories"] });
    queryClient.invalidateQueries({ queryKey: ["products"] });
  };
}

function errorMessage(error: unknown) {
  return error instanceof Error ? error.message : "Ocurrió un error";
}

export function useCreateCategory() {
  const refresh = useRefreshCategories();
  return useMutation({
    mutationFn: createCategoryApi,
    onSuccess: () => {
      refresh();
      toast.success("Categoría creada");
    },
    onError: (error) => toast.error(errorMessage(error)),
  });
}

export function useUpdateCategory() {
  const refresh = useRefreshCategories();
  return useMutation({
    mutationFn: ({ categoryId, data }: { categoryId: number; data: UpdateCategoryInput }) =>
      updateCategoryApi(categoryId, data),
    onSuccess: () => {
      refresh();
      toast.success("Categoría actualizada");
    },
    onError: (error) => toast.error(errorMessage(error)),
  });
}

export function useSetCategoryPublic() {
  const refresh = useRefreshCategories();
  return useMutation({
    mutationFn: ({ categoryId, isPublic }: { categoryId: number; isPublic: boolean }) =>
      setCategoryPublicApi(categoryId, isPublic),
    onSuccess: (_data, variables) => {
      refresh();
      toast.success(
        variables.isPublic
          ? "Categoría publicada en el catálogo"
          : "Categoría oculta del catálogo",
      );
    },
    onError: (error) => toast.error(errorMessage(error)),
  });
}

export function useDeleteCategory() {
  const refresh = useRefreshCategories();
  return useMutation({
    mutationFn: (categoryId: number) => deleteCategoryApi(categoryId),
    onSuccess: () => {
      refresh();
      toast.success("Categoría eliminada");
    },
    onError: (error) => toast.error(errorMessage(error)),
  });
}
