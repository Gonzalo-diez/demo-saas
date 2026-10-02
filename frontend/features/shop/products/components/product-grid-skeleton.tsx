import { ProductCardSkeleton } from "@/features/shop/products/components/product-card-skeleton"

type ProductGridSkeletonProps = {
  count?: number
  className?: string
}

export function ProductGridSkeleton({
  count = 12,
  className = "",
}: ProductGridSkeletonProps) {
  return (
    <div
      className={`grid grid-cols-2 gap-4 md:grid-cols-3 xl:grid-cols-4 ${className}`.trim()}
    >
      {Array.from({ length: count }).map((_, i) => (
        <ProductCardSkeleton key={i} />
      ))}
    </div>
  )
}