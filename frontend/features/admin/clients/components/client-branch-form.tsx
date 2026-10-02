"use client";

import { useEffect } from "react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import type {
  ClientBranch,
  CreateClientBranchInput,
} from "@/features/admin/clients/types";
import { useCreateClientBranch } from "@/features/admin/clients/hooks/use-create-client-branch";
import { useUpdateClientBranch } from "@/features/admin/clients/hooks/use-update-client-branch";

type ClientBranchFormProps = {
  clientId: number;
  branch?: ClientBranch | null;
  onSuccess?: () => void;
  onCancel?: () => void;
};

type FormValues = {
  name: string;
  address: string;
  city: string;
  lat: string;
  lng: string;
  contact_name: string;
  contact_phone: string;
  reference: string;
};

export function ClientBranchForm({
  clientId,
  branch,
  onSuccess,
  onCancel,
}: ClientBranchFormProps) {
  const createBranch = useCreateClientBranch();
  const updateBranch = useUpdateClientBranch();

  const { register, handleSubmit, reset, formState: { errors } } = useForm<FormValues>({
    defaultValues: {
      name: "",
      address: "",
      city: "",
      lat: "",
      lng: "",
      contact_name: "",
      contact_phone: "",
      reference: "",
    },
  });

  useEffect(() => {
    reset({
      name: branch?.name ?? "",
      address: branch?.address ?? "",
      city: branch?.city ?? "",
      lat: branch?.lat != null ? String(branch.lat) : "",
      lng: branch?.lng != null ? String(branch.lng) : "",
      contact_name: branch?.contact_name ?? "",
      contact_phone: branch?.contact_phone ?? "",
      reference: branch?.reference ?? "",
    });
  }, [branch, reset]);

  async function onSubmit(values: FormValues) {
    const payload: CreateClientBranchInput = {
      name: values.name,
      address: values.address || null,
      city: values.city || null,
      lat: values.lat ? Number(values.lat) : null,
      lng: values.lng ? Number(values.lng) : null,
      contact_name: values.contact_name || null,
      contact_phone: values.contact_phone || null,
      reference: values.reference || null,
      is_main: branch?.is_main ?? false,
    };

    try {
      if (branch) {
        await updateBranch.mutateAsync({
          clientId,
          branchId: branch.id,
          data: payload,
        });
        toast.success("Sucursal actualizada");
      } else {
        await createBranch.mutateAsync({
          clientId,
          data: payload,
        });
        toast.success("Sucursal creada");
      }

      reset();
      onSuccess?.();
    } catch (error) {
      toast.error(
        error instanceof Error ? error.message : "No se pudo guardar la sucursal"
      );
    }
  }

  const isPending = createBranch.isPending || updateBranch.isPending;

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4 rounded-xl border p-4">
      <div className="grid gap-4 md:grid-cols-2">
        <div className="space-y-1.5">
          <label className="text-sm font-medium">Nombre sucursal</label>
          <Input {...register("name", { required: "El nombre es obligatorio" })} />
          {errors.name && <p className="text-sm text-destructive">{errors.name.message}</p>}
        </div>

        <div className="space-y-1.5">
          <label className="text-sm font-medium">Ciudad</label>
          <Input {...register("city")} />
        </div>
      </div>

      <div className="space-y-1.5">
        <label className="text-sm font-medium">Dirección</label>
        <Textarea {...register("address")} rows={3} />
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <div className="space-y-1.5">
          <label className="text-sm font-medium">Latitud</label>
          <Input type="number" step="any" {...register("lat")} />
        </div>
        <div className="space-y-1.5">
          <label className="text-sm font-medium">Longitud</label>
          <Input type="number" step="any" {...register("lng")} />
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <div className="space-y-1.5">
          <label className="text-sm font-medium">Contacto</label>
          <Input {...register("contact_name")} />
        </div>
        <div className="space-y-1.5">
          <label className="text-sm font-medium">Teléfono</label>
          <Input {...register("contact_phone")} />
        </div>
      </div>

      <div className="space-y-1.5">
        <label className="text-sm font-medium">Referencia</label>
        <Input {...register("reference")} />
      </div>

      <div className="flex gap-2 justify-end">
        {onCancel ? (
          <Button type="button" variant="outline" onClick={onCancel}>
            Cancelar
          </Button>
        ) : null}
        <Button type="submit" disabled={isPending}>
          {isPending ? "Guardando..." : branch ? "Actualizar sucursal" : "Agregar sucursal"}
        </Button>
      </div>
    </form>
  );
}