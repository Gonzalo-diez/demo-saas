"use client";

import { useState } from "react";
import { FileSpreadsheet, PackagePlus, FileText } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogTrigger,
} from "@/components/ui/dialog";
import { ResponsiveTabs, TabItem } from "@/components/ui/responsive-tabs";
import { CreateProductForm } from "@/features/admin/products/components/create-product-form";
import { ImportProductsCard } from "@/features/admin/products/components/import-products-card";
import { GenerateExcelFromPdfCard } from "@/features/admin/products/components/generate-excel-from-pdf-card";

export function CreateProductDialog() {
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
          <CreateProductForm onSuccess={handleClose} />
        </div>
      ),
    },
    {
      value: "import",
      label: "Importar Excel",
      icon: FileSpreadsheet,
      content: (
        <div className="mx-auto max-w-4xl">
          <ImportProductsCard onSuccess={handleClose} />
        </div>
      ),
    },
    {
      value: "generate",
      label: "Generar Excel de PDF",
      icon: FileText,
      content: <GenerateExcelFromPdfCard onSuccess={handleClose} />,
    },
  ];

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button className="w-full sm:w-auto">
          <PackagePlus className="mr-2 h-4 w-4" />
          Nuevo producto
        </Button>
      </DialogTrigger>

      <DialogContent className="max-h-[90vh] overflow-y-auto px-4 sm:max-w-5xl sm:px-6">
        <DialogHeader>
          <DialogTitle>Productos</DialogTitle>
          <DialogDescription>
            Creá un producto manualmente o importá varios desde Excel.
          </DialogDescription>
        </DialogHeader>

        <ResponsiveTabs
          tabs={tabs}
          activeTab={activeTab}
          onTabChange={setActiveTab}
          tabsListClassName="sm:max-w-2xl sm:grid-cols-3"
        />
      </DialogContent>
    </Dialog>
  );
}