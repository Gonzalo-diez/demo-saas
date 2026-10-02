export function ProductCardSkeleton() {
  return (
    <article className="overflow-hidden rounded-xl border bg-card shadow-sm animate-pulse">
      <div className="aspect-square w-full bg-muted" />

      <div className="space-y-3 p-4">
        <div className="h-4 w-3/4 rounded bg-muted" />
        <div className="h-4 w-1/2 rounded bg-muted" />
        <div className="h-5 w-1/3 rounded bg-muted" />

        <div className="flex gap-2 pt-2">
          <div className="h-10 flex-1 rounded bg-muted" />
          <div className="h-10 w-10 rounded bg-muted" />
        </div>
      </div>
    </article>
  )
}