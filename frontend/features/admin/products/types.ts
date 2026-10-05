export type Product = {
  id: number;
  sku: string;
  name: string;
  name_normalized: string;
  description: string | null;
  brand: string | null;
  brand_normalized: string;
  category: string;
  category_id: number | null;
  category_normalized: string;
  is_public: boolean;
  slug: string;
  unit_cost: number;
  unit_price: number;
  /** % de remarque sobre el costo con el que se calculó el precio (si se usó). */
  markup_percent: number | null;
  currency: string;
  stock_current: number;
  stock_min: number;
  image_url: string | null;
  is_active: boolean;
  status: "DRAFT" | "ACTIVE" | "INACTIVE"; 
  created_at: string;
  updated_at: string;
};

export type PaginatedProductsResponse = {
  items: Product[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
};

// Basado en tu ProductCreate de Pydantic
export type CreateProductInput = {
  name: string;
  brand?: string | null;
  category?: string | null;
  /** Categoría elegida (de /api/categories). Es lo normal; `category` (texto) queda para importaciones. */
  category_id?: number | null;
  /** Visible en el catálogo de la tienda (además de que la categoría sea pública). */
  is_public?: boolean;
  unit_cost: number;
  /** Precio de venta. No se manda si se usa `markup_percent` (el backend lo calcula y redondea). */
  unit_price?: number;
  /** % de remarque sobre el costo: costo 200 + 40% = 280, redondeado al peso entero. */
  markup_percent?: number;
  /** Vencimiento del stock inicial (necesita stock_current > 0). Solo en el alta. */
  expiry_date?: string | null;
  description?: string | null;
  currency?: string | null;
  stock_current?: number;
  stock_min?: number;
  sku?: string | null;
  image_url?: string | null;
};

export type UpdateProductInput = Partial<CreateProductInput>;

// --- Tipos para la UI de búsqueda y filtros ---
export type ProductStatusFilter = "all" | "active" | "inactive" | "draft";

export type ProductSort =
  | "name-asc"
  | "name-desc"
  | "price-asc"
  | "price-desc"
  | "";

// --- Tipos para el flujo de Importación (Excel/CSV) ---
export type ImportMode = "upsert" | "create" | "update";

export type ProductImportRow = {
  sku: string;
  name: string;
  description: string | null;
  brand: string;
  category: string;
  unit_cost: number;
  unit_price: number;
  stock_current: number;
  stock_min: number;
  image_url: string | null;
  is_active: boolean | null;
};

export type ProductImportRowError = {
  row_number: number;
  data: Record<string, unknown>;
  errors: string[];
};

export type ProductImportPreviewResponse = {
  total_rows: number;
  valid_rows: number;
  invalid_rows: number;
  rows_valid: ProductImportRow[];
  rows_invalid: ProductImportRowError[];
};

export type ProductImportCommitRequest = {
  rows: ProductImportRow[];
  mode: ImportMode;
};

export type ProductImportCommitResponse = {
  total: number;
  created: number;
  updated: number;
  failed: number;
  errors: string[];
};

export type UploadedImageResponse = {
  url: string;
  public_id: string
  width: number
  height: number
  format: string
  bytes: number
  original_filename: string;
}

