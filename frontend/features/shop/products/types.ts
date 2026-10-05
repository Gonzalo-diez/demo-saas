export type ShopProduct = {
  id: number;
  slug: string;
  name: string;
  description: string | null;
  brand: string | null;
  category: string | null;
  category_id?: number | null;
  unit_price: number;
  currency: string;
  image_url: string | null;
  sku: string | null;
  /** La vista de tienda solo devuelve productos publicados: puede no venir. */
  is_active?: boolean;
  stock_current: number;
  is_in_stock?: boolean;
  /** La vista de tienda no los incluye (solo el personal ve las fechas). */
  created_at?: string;
  updated_at?: string;
};

// Respuesta de la API para el catálogo
export type ShopPaginatedResponse = {
  items: ShopProduct[];
  total: number;
  page: number;
  page_size: number;
  total_pages?: number;
};

// Estado del producto dentro del Carrito de Compras
export type CartItem = ShopProduct & {
  quantity: number;
  subtotal: number;
};

// Filtros que el cliente puede aplicar en la tienda
export type ShopFilters = {
  category?: string;
  brand?: string;
  min_price?: number;
  max_price?: number;
  search?: string;
};

// Ordenamiento en la UI
export type ShopSort = 
  | "newest" 
  | "price-low" 
  | "price-high" 
  | "name-asc";

// Parámetros para la consulta a la API
export type GetProductsShopParams = {
  search?: string;
  brand?: string;
  category?: string;
  category_id?: number;
  is_active?: boolean;
  page?: number;
  page_size?: number;
  sort?: "name-asc" | "name-desc" | "price-asc" | "price-desc";
  catalog_only?: boolean;
};