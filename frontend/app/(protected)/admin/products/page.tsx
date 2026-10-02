import { CreateProductDialog } from "@/features/admin/products/components/create-product-dialog";
import { ProductsList } from "@/features/admin/products/components/products-list";

export default function ProductsPage() {
  return (
    <div className="space-y-4">
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <h2 className="text-2xl font-semibold">Productos</h2>
          <p className="text-sm text-muted-foreground">
            Gestión de productos del sistema.
          </p>
        </div>
        
        <CreateProductDialog />
      </div>

      <ProductsList />
    </div>
  );
}