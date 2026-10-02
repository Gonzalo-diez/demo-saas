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
import { CreateSalesRepForm } from "@/features/admin/sales-reps/components/create-sales-rep-form";
import { ImportSalesRepsCard } from "@/features/admin/sales-reps/components/import-sales-reps-card";

export function CreateSalesRepDialog() {
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
          <CreateSalesRepForm onSuccess={handleClose} />
        </div>
      ),
    },
    {
      value: "import",
      label: "Importar Excel",
      icon: FileSpreadsheet,
      content: (
        <div className="mx-auto max-w-4xl">
          <ImportSalesRepsCard onSuccess={handleClose} />
        </div>
      ),
    },
  ];

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button className="w-full sm:w-auto">Nuevo vendedor</Button>
      </DialogTrigger>

      <DialogContent className="max-h-[90vh] overflow-y-auto px-4 sm:max-w-5xl sm:px-6">
        <DialogHeader>
          <DialogTitle>Nuevo vendedor</DialogTitle>
          <DialogDescription>
            Completá los datos para crear un nuevo vendedor.
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