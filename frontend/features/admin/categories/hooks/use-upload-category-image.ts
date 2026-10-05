"use client";

import { useMutation } from "@tanstack/react-query";
import { uploadCategoryImageApi } from "@/features/admin/categories/apis/categories-api";

export function useUploadCategoryImage() {
  return useMutation({
    mutationFn: (file: File) => uploadCategoryImageApi(file),
  });
}
