"use client";

import { useState } from "react";
import { FileSpreadsheet, PackagePlus } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { ResponsiveTabs, TabItem } from "@/components/ui/responsive-tabs";
import { CreateSupplierForm } from "@/features/admin/suppliers/components/create-supplier-form";
import { ImportSuppliersCard } from "@/features/admin/suppliers/components/import-suppliers-card";

export function CreateSupplierDialog() {
  const [open, setOpen] = useState(false);
  const [activeTab, setActiveTab] = useState("manual");

  const handleClose = () => setOpen(false);

  const tabs: TabItem[] = [
    {
      value: "manual",
      label: "Carga manual",
      icon: PackagePlus,
      content: (
        <div className="mx-auto max-w-2xl rounded-2xl border bg-card p-4 shadow-sm sm:p-6">
          <CreateSupplierForm onSuccess={handleClose} />
        </div>
      ),
    },
    {
      value: "import",
      label: "Importar Excel",
      icon: FileSpreadsheet,
      content: (
        <div className="mx-auto max-w-4xl">
          <ImportSuppliersCard onSuccess={handleClose} />
        </div>
      ),
    },
  ];

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button type="button" className="w-full sm:w-auto">
          Nuevo proveedor
        </Button>
      </DialogTrigger>

      <DialogContent className="max-h-[90vh] overflow-y-auto px-4 sm:max-w-2xl sm:px-6">
        <DialogHeader>
          <DialogTitle>Crear proveedor</DialogTitle>
          <DialogDescription>
            Completá los datos del proveedor para registrarlo en el sistema.
          </DialogDescription>
        </DialogHeader>

        <ResponsiveTabs
          tabs={tabs}
          activeTab={activeTab}
          onTabChange={setActiveTab}
        />
      </DialogContent>
    </Dialog>
  );
}