"use client";

import { Plus } from "lucide-react";
import { Button } from "@/components/ui/button";
import { PlatformAdminFormDialog } from "@/features/platform/components/platform-admin-form-dialog";
import { PlatformAdminsList } from "@/features/platform/components/platform-admins-list";

export default function PlatformAdminsPage() {
  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
        <div>
          <h2 className="text-2xl font-bold">Administradores</h2>
          <p className="text-sm text-muted-foreground">
            Personas que pueden gestionar la plataforma y dar de alta distribuidoras.
          </p>
        </div>

        <PlatformAdminFormDialog
          trigger={
            <Button className="w-full sm:w-auto">
              <Plus className="mr-2 h-4 w-4" />
              Nuevo administrador
            </Button>
          }
        />
      </div>

      <PlatformAdminsList />
    </div>
  );
}
