/** Espejo de CategoryAdminResponse (app/schemas/category_schema.py). */
export type Category = {
  id: number;
  name: string;
  slug: string;
  description: string | null;
  /** Imagen de la categoría en la tienda. Obligatoria si la categoría es pública. */
  image_url: string | null;
  /** Visible para los clientes en el catálogo. Si es false, sus productos son solo B2B interno. */
  is_public: boolean;
  /** Los pedidos online con productos de esta categoría piden DNI + mayoría de edad. */
  requires_age_verification: boolean;
  product_count: number;
  created_at: string;
  updated_at: string;
};

export type CategoriesResponse = {
  items: Category[];
  total: number;
};

export type CategoriesQueryParams = {
  search?: string;
  is_public?: boolean;
};

export type CreateCategoryInput = {
  name: string;
  description?: string | null;
  image_url?: string | null;
  is_public: boolean;
  requires_age_verification: boolean;
};

export type UpdateCategoryInput = Partial<CreateCategoryInput>;
