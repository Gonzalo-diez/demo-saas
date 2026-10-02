"use client";

import { useState } from "react";
import { CirclePlus } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { CreatePurchaseQuoteForm } from "@/features/admin/purchase-quotes/components/create-purchase-quote-form";

export function CreatePurchaseQuoteDialog() {
  const [open, setOpen] = useState(false);

  function handleClose() {
    setOpen(false);
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button>
          <CirclePlus className="mr-2 h-4 w-4" />
          Nuevo presupuesto de compra
        </Button>
      </DialogTrigger>

      <DialogContent className="max-h-[90vh] overflow-y-auto sm:max-w-4xl">
        <DialogHeader>
          <DialogTitle>Crear presupuesto de compra</DialogTitle>
          <DialogDescription>
            Cotización de un proveedor, sin efecto en stock ni cuenta corriente. No se puede
            convertir directamente en remito.
          </DialogDescription>
        </DialogHeader>

        <div className="mx-auto max-w-2xl rounded-2xl border bg-card p-6 shadow-sm">
          <CreatePurchaseQuoteForm onSuccess={handleClose} />
        </div>
      </DialogContent>
    </Dialog>
  );
}
