/** Espejo de AdminResponse (app/schemas/admin_schema.py): administrador de la PLATAFORMA. */
export type PlatformAdmin = {
  id: number;
  name: string;
  email: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

export type PlatformLoginInput = {
  email: string;
  password: string;
};

export type CreatePlatformAdminInput = {
  name: string;
  email: string;
  password: string;
  is_active?: boolean;
};

export type UpdatePlatformAdminInput = Partial<CreatePlatformAdminInput>;

/** Espejo de TenantResponse: una distribuidora. */
export type Tenant = {
  id: number;
  name: string;
  slug: string;
  /** Host de la tienda de la distribuidora (ej. tienda.distri-oeste.com). */
  domain: string;
  logo_url: string | null;
  email: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

export type PaginatedTenants = {
  items: Tenant[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
};

export type TenantsQueryParams = {
  page?: number;
  page_size?: number;
  search?: string;
  is_active?: boolean;
  sort?: "name" | "slug" | "created_at";
};

/** Espejo de TenantProvision: alta de distribuidora (+ su primer administrador, opcional). */
export type CreateTenantInput = {
  name: string;
  slug: string;
  /** Dominio o URL de la tienda; el backend guarda solo el host. */
  domain: string;
  logo_url?: string | null;
  email?: string | null;
  admin_name?: string | null;
  admin_email?: string | null;
  admin_password?: string | null;
};

export type UpdateTenantInput = {
  name?: string;
  slug?: string;
  domain?: string;
  logo_url?: string | null;
  email?: string | null;
};
