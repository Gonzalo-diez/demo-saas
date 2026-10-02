import { InventoryMovementsList } from "@/features/admin/inventory-movements/components/inventory-movements-list";

export default function InventoryMovementsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-semibold">Movimientos de inventario</h2>
        <p className="text-sm text-muted-foreground">
          Revisá el historial de entradas y salidas de stock por producto y tipo de referencia.
        </p>
      </div>

      <InventoryMovementsList />
    </div>
  );
}