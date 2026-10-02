"use client";

import { useMutation } from "@tanstack/react-query";
import { uploadAdminProductImage } from "@/features/admin/products/apis/products-api";

export function useUploadProductImage() {
  return useMutation({
    mutationFn: (file: File) => uploadAdminProductImage(file),
  });
}