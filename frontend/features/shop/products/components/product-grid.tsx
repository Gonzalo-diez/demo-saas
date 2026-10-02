import { ProductCard } from "@/features/shop/products/components/product-card"
import type { ShopProduct } from "@/features/shop/products/types"

type ProductGridProps = {
  products: ShopProduct[]
  salesRepId?: number
  className?: string
}

export function ProductGrid({ products, salesRepId, className = "" }: ProductGridProps) {
  return (
    <div className={`grid grid-cols-2 gap-4 md:grid-cols-3 xl:grid-cols-4 ${className}`.trim()}>
      {products.map((product) => (
        <ProductCard key={product.id} product={product} salesRepId={salesRepId} />
      ))}
    </div>
  )
}