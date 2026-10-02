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

import { CreateOrderForm } from "@/features/admin/orders/components/create-order-form";

export function CreateOrderDialog() {
  const [open, setOpen] = useState(false);

  function handleClose() {
    setOpen(false);
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button className="w-full sm:w-auto">
          <CirclePlus className="mr-2 h-4 w-4" />
          Nueva orden
        </Button>
      </DialogTrigger>

      <DialogContent className="max-h-[90vh] overflow-y-auto px-4 sm:max-w-6xl sm:px-6">
        <DialogHeader>
          <DialogTitle>Crear orden</DialogTitle>
          <DialogDescription>
            Seleccioná un cliente y agregá los productos del pedido.
          </DialogDescription>
        </DialogHeader>

        <div className="rounded-2xl border bg-card p-4 shadow-sm sm:p-6">
          <CreateOrderForm onSuccess={handleClose} />
        </div>
      </DialogContent>
    </Dialog>
  );
}