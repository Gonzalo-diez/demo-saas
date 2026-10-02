import { ProductGridSkeleton } from "@/features/shop/products/components/product-grid-skeleton"

export default function Loading() {
  return (
    <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 sm:py-10">
      <div className="grid gap-8 lg:grid-cols-[280px_1fr]">

        <div className="hidden lg:block space-y-4">
          <div className="h-6 w-32 rounded bg-muted animate-pulse" />
          <div className="h-40 rounded bg-muted animate-pulse" />
        </div>

        <div className="space-y-6">
          <ProductGridSkeleton count={12} />
        </div>

      </div>
    </main>
  )
}