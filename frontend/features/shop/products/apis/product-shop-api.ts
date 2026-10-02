import { apiFetch } from "@/lib/fetcher"
import type {
  ShopProduct,
  ShopPaginatedResponse,
  GetProductsShopParams,
} from "@/features/shop/products/types"

export async function getProductsResponse(
  params: GetProductsShopParams = {}
): Promise<ShopPaginatedResponse> {
  // En el shop forzamos catalog_only: true por defecto
  const shopQueryParams: GetProductsShopParams = {
    catalog_only: true,
    ...params,
  }

  const searchParams = new URLSearchParams()

  Object.entries(shopQueryParams).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") {
      searchParams.set(key, String(value))
    }
  })

  const query = searchParams.toString()
  const path = query ? `/api/products?${query}` : "/api/products"

  return apiFetch<ShopPaginatedResponse>(path)
}

export async function getProducts(
  params: GetProductsShopParams = {}
): Promise<ShopProduct[]> {
  const data = await getProductsResponse(params)
  return data.items
}

export async function getAllProducts(
  params: Omit<GetProductsShopParams, "page" | "page_size"> = {}
): Promise<ShopProduct[]> {
  const firstPage = await getProductsResponse({
    ...params,
    page: 1,
    page_size: 100,
  })

  const totalPages = Math.ceil(firstPage.total / firstPage.page_size)

  if (totalPages <= 1) {
    return firstPage.items
  }

  const restPages = await Promise.all(
    Array.from({ length: totalPages - 1 }, (_, index) =>
      getProductsResponse({
        ...params,
        page: index + 2,
        page_size: 100,
      })
    )
  )

  return [
    ...firstPage.items,
    ...restPages.flatMap((page) => page.items),
  ]
}

export async function getProductBySlug(slug: string): Promise<ShopProduct | null> {
  const products = await getAllProducts({ is_active: true })
  const product = products.find((item) => item.slug === slug)
  return product ?? null
}