"use client";

import { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogTrigger,
} from "@/components/ui/dialog";

import { Button } from "@/components/ui/button";
import type { Client } from "@/features/admin/clients/types";
import { ClientBranchesManager } from "@/features/admin/clients/components/client-branches-manager";
import { GitBranch } from "lucide-react";

type Props = {
  client: Client;
};

export function EditClientBranchesDialog({ client }: Props) {
  const [open, setOpen] = useState(false);

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button type="button" variant="outline" size="sm" className="w-full sm:w-auto">
          <GitBranch className="mr-2 h-4 w-4" />
          Sucursales
        </Button>
      </DialogTrigger>

      <DialogContent className="max-h-[90vh] overflow-y-auto px-4 sm:max-w-5xl sm:px-6">
        <DialogHeader>
          <DialogTitle>
            Sucursales de {client.name}
          </DialogTitle>
          <DialogDescription>
            Gestioná las sucursales del cliente.
          </DialogDescription>
        </DialogHeader>

        <div className="rounded-2xl border bg-card p-4 shadow-sm sm:p-6">
          <ClientBranchesManager client={client} />
        </div>
      </DialogContent>
    </Dialog>
  );
}