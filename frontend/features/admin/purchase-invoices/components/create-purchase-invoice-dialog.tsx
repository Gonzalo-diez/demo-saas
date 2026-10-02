"use client";

import { useState } from "react";
import { CirclePlus, FileSpreadsheet, PackagePlus } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  Tabs,
  TabsList,
  TabsTrigger,
  TabsContent,
} from "@/components/ui/tabs";
import { PurchaseInvoiceImportCard } from "@/features/admin/purchase-invoices/components/purchase-invoice-import-card";
import { CreatePurchaseInvoiceForm } from "@/features/admin/purchase-invoices/components/create-purchase-invoice-form";

export function CreatePurchaseInvoiceDialog() {
  const [open, setOpen] = useState(false);

  function handleClose() {
    setOpen(false);
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button>
          <CirclePlus className="mr-2 h-4 w-4" />
          Nuevo remito de compra
        </Button>
      </DialogTrigger>

      <DialogContent className="max-h-[90vh] overflow-y-auto sm:max-w-4xl">
        <DialogHeader>
          <DialogTitle>Crear remito de compra</DialogTitle>
          <DialogDescription>
            Cargá el remito manualmente seleccionando proveedor y productos.
          </DialogDescription>
        </DialogHeader>

        <Tabs defaultValue="manual" className="w-full">
          <TabsList className="grid w-full max-w-md grid-cols-2">
            <TabsTrigger value="manual">
              <PackagePlus className="mr-2 h-4 w-4" />
              Carga Manual
            </TabsTrigger>
            <TabsTrigger value="import">
              <FileSpreadsheet className="mr-2 h-4 w-4" />
              Importar pdf
            </TabsTrigger>
          </TabsList>

          <TabsContent value="manual" className="mt-6">
            <div className="mx-auto max-w-2xl rounded-2xl border bg-card p-6 shadow-sm">
              <CreatePurchaseInvoiceForm onSuccess={handleClose} />
            </div>
          </TabsContent>

          <TabsContent value="import" className="mt-6">
            <PurchaseInvoiceImportCard onSuccess={handleClose} />
          </TabsContent>
        </Tabs>
      </DialogContent>
    </Dialog>
  );
}