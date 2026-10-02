import type { ShopProduct } from "@/features/shop/products/types"
import type { Product } from "@/types/products"
import { resolveCategory } from "@/lib/utils/category-normalizer"

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
  const resolvedCategory = resolveCategory(shopProduct.category)

  return {
    id: shopProduct.id,
    name: shopProduct.name,
    slug: shopProduct.slug,
    description: shopProduct.description ?? "",
    brand: shopProduct.brand,

    category: resolvedCategory?.name ?? shopProduct.category,
    categorySlug: resolvedCategory?.slug ?? safeSlug(shopProduct.category),

    unit_price: Number(shopProduct.unit_price),
    currency: shopProduct.currency,

    stock_current: shopProduct.stock_current,
    sku: shopProduct.sku ?? null,

    image_url: shopProduct.image_url ?? "/placeholder-product.png",
    isActive: shopProduct.is_active,

    createdAt: shopProduct.created_at,
    updatedAt: shopProduct.updated_at,
  }
}