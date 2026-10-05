export type Product = {
  id: number
  name: string
  slug: string
  description: string
  brand: string
  category: string
  categorySlug: string
  categoryId?: number | null
  unit_price: number
  currency: string
  stock_current: number
  sku: string | null
  image_url: string
  isActive: boolean
  createdAt: string
  updatedAt: string
}