/**
 * Espejo de TenantPublicResponse (GET /api/tenants/slug/{slug} y
 * GET /api/tenants/by-domain/{host}).
 */
export type TenantPublic = {
  id: number;
  name: string;
  slug: string;
  /** Host de la tienda de esta distribuidora (ej. tienda.distri-oeste.com). */
  domain: string;
  logo_url: string | null;
};
