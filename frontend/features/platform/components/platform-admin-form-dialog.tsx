"use client";

import { useState, type ReactNode } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  platformAdminSchema,
  type PlatformAdminFormValues,
} from "@/features/platform/schemas/platform-schemas";
import { useCreatePlatformAdmin } from "@/features/platform/hooks/use-platform-admins";

function AdminForm({ onDone }: { onDone: () => void }) {
  const createAdmin = useCreatePlatformAdmin();
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<PlatformAdminFormValues>({
    resolver: zodResolver(platformAdminSchema),
    defaultValues: { name: "", email: "", password: "" },
  });

  const onSubmit = async (values: PlatformAdminFormValues) => {
    try {
      await createAdmin.mutateAsync(values);
      onDone();
    } catch {
      // el toast de error lo muestra el hook
    }
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <div className="space-y-1.5">
        <Label>Nombre *</Label>
        <Input placeholder="Nombre y apellido" {...register("name")} />
        {errors.name && <p className="text-sm text-destructive">{errors.name.message}</p>}
      </div>
      <div className="space-y-1.5">
        <Label>Email *</Label>
        <Input type="email" autoComplete="off" placeholder="admin@plataforma.com" {...register("email")} />
        {errors.email && <p className="text-sm text-destructive">{errors.email.message}</p>}
      </div>
      <div className="space-y-1.5">
        <Label>Contraseña *</Label>
        <Input type="password" autoComplete="new-password" placeholder="Mínimo 6 caracteres" {...register("password")} />
        {errors.password && <p className="text-sm text-destructive">{errors.password.message}</p>}
      </div>

      <div className="flex justify-end gap-2 pt-2">
        <Button type="button" variant="outline" onClick={onDone} disabled={createAdmin.isPending}>
          Cancelar
        </Button>
        <Button type="submit" disabled={createAdmin.isPending}>
          {createAdmin.isPending ? "Guardando..." : "Crear administrador"}
        </Button>
      </div>
    </form>
  );
}

export function PlatformAdminFormDialog({ trigger }: { trigger: ReactNode }) {
  const [open, setOpen] = useState(false);

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>{trigger}</DialogTrigger>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Nuevo administrador</DialogTitle>
          <DialogDescription>
            Un administrador de plataforma puede crear y desactivar distribuidoras.
          </DialogDescription>
        </DialogHeader>
        <AdminForm onDone={() => setOpen(false)} />
      </DialogContent>
    </Dialog>
  );
}
