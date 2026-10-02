export type Product = {
  id: number;
  sku: string;
  name: string;
  name_normalized: string;
  description: string | null;
  brand: string | null;
  brand_normalized: string;
  category: string;
  category_normalized: string;
  slug: string;
  unit_cost: number;
  unit_price: number;
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
  unit_cost: number;
  unit_price: number;
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

// --- Categorías para el alta/edición manual (GET /products/categories) ---
export type CategoryOption = {
  value: string;
  label: string;
};

export type ProductCategoriesResponse = {
  /** Categorías seteadas: se muestran en el catálogo online. */
  catalog: CategoryOption[];
  /** Categorías libres ya en uso: solo venta B2B. */
  free: string[];
  /** alias normalizado -> categoría canónica de catálogo. */
  catalog_aliases: Record<string, string>;
};
