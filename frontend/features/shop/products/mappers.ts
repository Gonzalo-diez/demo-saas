import type { ShopProduct } from "@/features/shop/products/types"
import type { Product } from "@/types/products"

function safeSlug(value: string | null | undefined): string {
  if (!value) return ""

  return value
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/[^a-z0-9\s-]/g, "")
    .trim()
    .replace(/\s+/g, "-")
}

export function mapApiProductToProduct(shopProduct: ShopProduct): Product {
  return {
    id: shopProduct.id,
    name: shopProduct.name,
    slug: shopProduct.slug,
    description: shopProduct.description ?? "",
    brand: shopProduct.brand ?? "",

    category: shopProduct.category ?? "",
    categorySlug: safeSlug(shopProduct.category),
    categoryId: shopProduct.category_id ?? null,

    unit_price: Number(shopProduct.unit_price),
    currency: shopProduct.currency,

    stock_current: shopProduct.stock_current,
    sku: shopProduct.sku ?? null,

    image_url: shopProduct.image_url ?? "/placeholder-product.png",
    // Todo lo que llega a la tienda está publicado y activo.
    isActive: shopProduct.is_active ?? true,

    createdAt: shopProduct.created_at ?? "",
    updatedAt: shopProduct.updated_at ?? "",
  }
}