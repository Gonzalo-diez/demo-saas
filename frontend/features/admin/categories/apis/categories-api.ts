import { apiFetch } from "@/lib/fetcher";
import type {
  CategoriesQueryParams,
  CategoriesResponse,
  Category,
  CreateCategoryInput,
  UpdateCategoryInput,
} from "@/features/admin/categories/types";
import type { UploadedImageResponse } from "@/features/admin/products/types";

export async function getCategoriesApi(params: CategoriesQueryParams = {}) {
  const searchParams = new URLSearchParams();
  if (params.search) searchParams.set("search", params.search);
  if (params.is_public !== undefined) {
    searchParams.set("is_public", String(params.is_public));
  }
  const query = searchParams.toString();

  return apiFetch<CategoriesResponse>(
    query ? `/api/categories/?${query}` : "/api/categories/",
    { method: "GET" },
  );
}

export async function createCategoryApi(data: CreateCategoryInput) {
  return apiFetch<Category>("/api/categories/", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function updateCategoryApi(categoryId: number, data: UpdateCategoryInput) {
  return apiFetch<Category>(`/api/categories/${categoryId}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export async function setCategoryPublicApi(categoryId: number, isPublic: boolean) {
  return apiFetch<Category>(
    `/api/categories/${categoryId}/${isPublic ? "publish" : "unpublish"}`,
    { method: "PATCH" },
  );
}

/** Sube la imagen de una categoría (Cloudinary); la URL devuelta va en `image_url`. */
export async function uploadCategoryImageApi(file: File) {
  const formData = new FormData();
  formData.append("file", file);

  return apiFetch<UploadedImageResponse>("/api/upload/category-image", {
    method: "POST",
    body: formData,
  });
}

export async function deleteCategoryApi(categoryId: number) {
  return apiFetch<null>(`/api/categories/${categoryId}`, { method: "DELETE" });
}
