import { getApiUrl } from "@/lib/api";
import { apiFetch, apiFetchBlob } from "@/lib/fetcher";
import type {
  CreateProductInput,
  PaginatedProductsResponse,
  Product,
  ProductImportCommitRequest,
  ProductImportCommitResponse,
  ProductImportPreviewResponse,
  ProductSort,
  ProductStatusFilter,
  UpdateProductInput,
  UploadedImageResponse,
} from "@/features/admin/products/types";

export type ProductsQueryParams = {
  page?: number;
  page_size?: number;
  search?: string;
  status?: ProductStatusFilter;
  brand?: string;
  category?: string; // Añadido: Vimos que el repo lo soporta
  sort?: ProductSort;
  catalog_only?: boolean;
};

/**
 * Construye la URL con Query Params para la lista de productos.
 */
function buildProductsQuery(params: ProductsQueryParams = {}) {
  const searchParams = new URLSearchParams();

  searchParams.set("page", String(params.page ?? 1));
  searchParams.set("page_size", String(params.page_size ?? 20)); // Ajustado a 20 como el repo

  if (params.search) searchParams.set("search", params.search);
  
  // Ajuste de lógica de status: 
  // Si en el backend usas "is_active" como bool, aquí convertimos "active" -> true
  if (params.status === "active") searchParams.set("is_active", "true");
  if (params.status === "inactive") searchParams.set("is_active", "false");
  
  if (params.brand) searchParams.set("brand", params.brand);
  if (params.category) searchParams.set("category", params.category);
  if (params.sort) searchParams.set("sort", params.sort);

  if (params.catalog_only !== undefined) {
    searchParams.set("catalog_only", String(params.catalog_only));
  }

  return `/api/products/?${searchParams.toString()}`;
}

// --- API FUNCTIONS ---

export async function getProductsApi(params: ProductsQueryParams = {}) {
  const adminQueryParams: ProductsQueryParams = {
    catalog_only: false,
    ...params,
  };

  return apiFetch<PaginatedProductsResponse>(buildProductsQuery(adminQueryParams), {
    method: "GET",
  });
}

export async function getProductApi(productId: number) {
  return apiFetch<Product>(`/api/products/${productId}`, {
    method: "GET",
  });
}

export async function createProductApi(data: CreateProductInput) {
  return apiFetch<Product>("/api/products/", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function updateProductApi(
  productId: number,
  data: UpdateProductInput
) {
  // Aseguramos que sea PATCH como definimos en la Route
  return apiFetch<Product>(`/api/products/${productId}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export async function toggleProductStatusApi(
  productId: number,
  nextStatus: "active" | "inactive"
) {
  // Ajuste de endpoints según tu lógica de repository
  const endpoint =
    nextStatus === "active"
      ? `/api/products/${productId}/reactivate`
      : `/api/products/${productId}/deactivate`;

  return apiFetch<Product>(endpoint, {
    method: "PATCH",
  });
}

/** Publica / oculta un producto del catálogo de la tienda (no toca su stock ni su estado). */
export async function setProductPublicApi(productId: number, isPublic: boolean) {
  return apiFetch<Product>(
    `/api/products/${productId}/${isPublic ? "publish" : "unpublish"}`,
    { method: "PATCH" },
  );
}

/**
 * Sube el archivo para obtener la previsualización (Válidos vs Inválidos)
 */
export async function previewProductsImportApi(file: File) {
  const formData = new FormData();
  formData.append("file", file);

  // Endpoint: /api/products/import/preview
  return apiFetch<ProductImportPreviewResponse>("/api/products/import/preview", {
    method: "POST",
    body: formData,
  });
}

/**
 * Confirma la importación de las filas validadas en el preview
 */
export async function commitProductsImportApi(
  data: ProductImportCommitRequest
) {
  // Endpoint: /api/products/import/commit
  return apiFetch<ProductImportCommitResponse>("/api/products/import/commit", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

/**
 * Extra: Importación directa (sin preview)
 */
export async function commitProductsImportFileApi(file: File, mode: string = "upsert") {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("mode", mode);

  return apiFetch<ProductImportCommitResponse>("/api/products/import/commit-file", {
    method: "POST",
    body: formData,
  });
}

/**
 * Descarga el Excel de ejemplo para importar productos
 */
export async function downloadProductImportSampleApi(): Promise<Blob> {
  return apiFetchBlob("/api/products/import/sample-excel", {
    method: "GET",
  });
}

export async function generateImportExcelFromPdfApi(file: File): Promise<Blob> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${getApiUrl()}/api/products/import/from-pdf`, {
    method: "POST",
    credentials: "include",
    body: formData,
  });

  if (!response.ok) {
    let message = "Error al procesar el PDF";
    try {
      const errorData = await response.json();
      message = errorData.detail ?? message;
    } catch {}
    throw new Error(message);
  }

  return response.blob();
}

export async function uploadAdminProductImage(
  file: File
): Promise<UploadedImageResponse> {
  const formData = new FormData();

  formData.append("file", file);

  return apiFetch<UploadedImageResponse>(
    "/api/upload/product-image",
    {
      method: "POST",
      body: formData,
    }
  );
}