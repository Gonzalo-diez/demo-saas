"use client";

import { useState } from "react";
import { FileSpreadsheet, PackagePlus } from "lucide-react";
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
import { CreateClientForm } from "@/features/admin/clients/components/create-client-form";
import { ImportClientsCard } from "@/features/admin/clients/components/import-clients-card";

export function CreateClientDialog() {
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
          <CreateClientForm onSuccess={handleClose} />
        </div>
      ),
    },
    {
      value: "import",
      label: "Importar Excel",
      icon: FileSpreadsheet,
      content: (
        <div className="mx-auto max-w-4xl">
          <ImportClientsCard onSuccess={handleClose} />
        </div>
      ),
    },
  ];

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button className="w-full sm:w-auto">
          <PackagePlus className="mr-2 h-4 w-4" />
          Nuevo cliente
        </Button>
      </DialogTrigger>

      <DialogContent className="max-h-[90vh] overflow-y-auto px-4 sm:max-w-5xl sm:px-6">
        <DialogHeader>
          <DialogTitle>Clientes</DialogTitle>
          <DialogDescription>
            Creá un cliente manualmente o importá varios desde Excel.
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