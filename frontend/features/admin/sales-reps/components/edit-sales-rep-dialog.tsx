"use client";

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { CreateSalesRepForm } from "@/features/admin/sales-reps/components/create-sales-rep-form";
import type { SalesRep } from "@/features/admin/sales-reps/types";

type EditSalesRepDialogProps = {
  open: boolean;
  salesRep: SalesRep | null;
  onClose: () => void;
};

export function EditSalesRepDialog({
  open,
  salesRep,
  onClose,
}: EditSalesRepDialogProps) {
  if (!salesRep) return null;

  return (
    <Dialog open={open} onOpenChange={(value) => !value && onClose()}>
      <DialogContent className="max-h-[90vh] overflow-y-auto px-4 sm:max-w-2xl sm:px-6">
        <DialogHeader>
          <DialogTitle>Editar vendedor</DialogTitle>
          <DialogDescription>
            Modificá los datos del vendedor y guardá los cambios.
          </DialogDescription>
        </DialogHeader>

        <div className="rounded-2xl border bg-card p-4 shadow-sm sm:p-6">
          <CreateSalesRepForm
            mode="edit"
            initialData={salesRep}
            onSuccess={onClose}
          />
        </div>
      </DialogContent>
    </Dialog>
  );
}