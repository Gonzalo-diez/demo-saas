import { CreateOrderDialog } from "@/features/admin/orders/components/create-order-dialog";
import { OrdersList } from "@/features/admin/orders/components/orders-list";

export default function OrdersPage() {
  return (
    <div className="space-y-4">
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Órdenes</h1>
          <p className="text-sm text-muted-foreground">
            Gestión de pedidos del sistema.
          </p>
        </div>

        <CreateOrderDialog />
      </div>

      <OrdersList />
    </div>
  );
}