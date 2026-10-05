/** Espejo de CategoryAdminResponse (GET /api/categories/). Un cliente solo recibe las públicas. */
export type ShopCategory = {
  id: number;
  name: string;
  slug: string;
  description: string | null;
  /** Portada de la categoría en el catálogo. */
  image_url: string | null;
  is_public: boolean;
  requires_age_verification: boolean;
  product_count: number;
};

export type ShopCategoriesResponse = {
  items: ShopCategory[];
  total: number;
};
