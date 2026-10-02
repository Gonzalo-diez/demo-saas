export function ProductsEmptyState() {
  return (
    <div className="rounded-xl border bg-background p-8 text-center shadow-sm">
      <h3 className="text-lg font-semibold">No hay productos</h3>
      <p className="mt-2 text-sm text-muted-foreground">
        Cuando existan productos cargados, aparecerán aquí.
      </p>
    </div>
  );
}