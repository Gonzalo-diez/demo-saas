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
import { CreateSalesQuoteForm } from "@/features/admin/sales-quotes/components/create-sales-quote-form";

export function CreateSalesQuoteDialog() {
  const [open, setOpen] = useState(false);

  function handleClose() {
    setOpen(false);
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button>
          <CirclePlus className="mr-2 h-4 w-4" />
          Nuevo presupuesto de venta
        </Button>
      </DialogTrigger>

      <DialogContent className="max-h-[90vh] overflow-y-auto sm:max-w-4xl">
        <DialogHeader>
          <DialogTitle>Crear presupuesto de venta</DialogTitle>
          <DialogDescription>
            Cotización para un cliente, sin efecto en stock ni cuenta corriente. No se puede
            convertir directamente en remito.
          </DialogDescription>
        </DialogHeader>

        <div className="mx-auto max-w-2xl rounded-2xl border bg-card p-6 shadow-sm">
          <CreateSalesQuoteForm onSuccess={handleClose} />
        </div>
      </DialogContent>
    </Dialog>
  );
}
