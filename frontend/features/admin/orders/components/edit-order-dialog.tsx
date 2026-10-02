"use client";

import { useState } from "react";
import { Pencil } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";

import { EditOrderB2BForm } from "@/features/admin/orders/components/edit-order-b2b-form";
import { EditOrderShopForm } from "@/features/admin/orders/components/edit-order-shop-form";
import type { AdminOrder } from "@/features/admin/orders/types";

type EditOrderDialogProps = {
  order: AdminOrder;
};

export function EditOrderDialog({ order }: EditOrderDialogProps) {
  const [open, setOpen] = useState(false);

  const isB2B = order.sales_type === "B2B";

  function handleClose() {
    setOpen(false);
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button variant="outline" size="sm">
          <Pencil className="mr-2 h-3.5 w-3.5" />
          Editar
        </Button>
      </DialogTrigger>

      <DialogContent className="max-h-[90vh] overflow-y-auto px-4 sm:max-w-6xl sm:px-6">
        <DialogHeader>
          <DialogTitle>
            Editar orden #{order.id}
            <span
              className={`ml-2 text-xs font-bold uppercase px-2 py-0.5 rounded-full ${
                isB2B
                  ? "bg-chart-4/15 text-chart-4"
                  : "bg-chart-3/15 text-chart-3"
              }`}
            >
              {isB2B ? "B2B" : "Online"}
            </span>
          </DialogTitle>
          <DialogDescription>
            {isB2B
              ? "Modificá la sucursal, referencia de entrega y los productos del pedido."
              : "Modificá los datos del cliente, la entrega y los productos del pedido."}
          </DialogDescription>
        </DialogHeader>

        <div className="rounded-2xl border bg-card p-4 shadow-sm sm:p-6">
          {isB2B ? (
            <EditOrderB2BForm order={order} onSuccess={handleClose} />
          ) : (
            <EditOrderShopForm order={order} onSuccess={handleClose} />
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}