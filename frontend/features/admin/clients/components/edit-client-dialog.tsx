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
import { CreateClientForm } from "@/features/admin/clients/components/create-client-form";
import type { Client } from "@/features/admin/clients/types";

type EditClientDialogProps = {
  client: Client;
};

export function EditClientDialog({ client }: EditClientDialogProps) {
  const [open, setOpen] = useState(false);

  function handleClose() {
    setOpen(false);
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button type="button" variant="outline" size="sm" className="w-full sm:w-auto">
          <Pencil className="mr-2 h-4 w-4" />
          Editar
        </Button>
      </DialogTrigger>

      <DialogContent className="max-h-[90vh] overflow-y-auto px-4 sm:max-w-3xl sm:px-6">
        <DialogHeader>
          <DialogTitle>Editar cliente</DialogTitle>
          <DialogDescription>
            Actualizá los datos generales del cliente.
          </DialogDescription>
        </DialogHeader>

        <div className="rounded-2xl border bg-card p-4 shadow-sm sm:p-6">
          <CreateClientForm
            mode="edit"
            initialData={client}
            onSuccess={handleClose}
          />
        </div>
      </DialogContent>
    </Dialog>
  );
}