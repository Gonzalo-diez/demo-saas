"use client";

import { CreateSalesRepDialog } from "@/features/admin/sales-reps/components/create-sales-rep-dialog";
import { SalesRepsList } from "@/features/admin/sales-reps/components/sales-reps-list";
import { useAuthStore } from "@/features/admin/auth/store/auth-store";

export default function SalesRepsPage() {
  const isSuperuser = useAuthStore((state) => state.user?.is_superuser ?? false);

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
        <div>
          <h2 className="text-2xl font-semibold">Vendedores</h2>
          <p className="text-sm text-muted-foreground">
            Gestión de vendedores del sistema.
          </p>
        </div>

        {isSuperuser && <CreateSalesRepDialog />}
      </div>

      <SalesRepsList />
    </div>
  );
}