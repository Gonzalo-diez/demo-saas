"use client";

import { Plus } from "lucide-react";
import { Button } from "@/components/ui/button";
import { TenantFormDialog } from "@/features/platform/components/tenant-form-dialog";
import { TenantsList } from "@/features/platform/components/tenants-list";

export default function PlatformTenantsPage() {
  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
        <div>
          <h2 className="text-2xl font-bold">Distribuidoras</h2>
          <p className="text-sm text-muted-foreground">
            Cada distribuidora es un espacio aislado: sus vendedores, clientes, productos y pedidos.
          </p>
        </div>

        <TenantFormDialog
          trigger={
            <Button className="w-full sm:w-auto">
              <Plus className="mr-2 h-4 w-4" />
              Nueva distribuidora
            </Button>
          }
        />
      </div>

      <TenantsList />
    </div>
  );
}
