import { CreateSupplierDialog } from "@/features/admin/suppliers/components/create-supplier-dialog";
import { SuppliersList } from "@/features/admin/suppliers/components/suppliers-list";

export default function SupplierPage() {
    return (
        <div className="space-y-6">
            <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
                <div>
                    <h2 className="text-2xl font-semibold">Proveedores</h2>
                    <p className="text-sm text-muted-foreground">
                        Registra proveedores
                    </p>
                </div>

                <CreateSupplierDialog />
            </div>

            <SuppliersList />
        </div>
    )
}