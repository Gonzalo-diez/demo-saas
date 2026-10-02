"use client";

import { useEffect } from "react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import { zodResolver } from "@hookform/resolvers/zod";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import {
  createSupplierSchema,
  updateSupplierSchema,
  type CreateSupplierFormInput,
  type CreateSupplierFormValues,
  type UpdateSupplierFormInput,
  type UpdateSupplierFormValues,
} from "@/features/admin/suppliers/schemas/supplier-schema";
import { useCreateSupplier } from "@/features/admin/suppliers/hooks/use-create-supplier";
import { useUpdateSupplier } from "@/features/admin/suppliers/hooks/use-update-supplier";
import type { Supplier } from "@/features/admin/suppliers/types";

type CreateSupplierFormProps = {
  onSuccess?: () => void;
  mode?: "create" | "edit";
  initialData?: Supplier | null;
};

export function CreateSupplierForm({
  onSuccess,
  mode = "create",
  initialData = null,
}: CreateSupplierFormProps) {
  const createSupplier = useCreateSupplier();
  const updateSupplier = useUpdateSupplier();

  const isEditMode = mode === "edit";

  const {
    register,
    handleSubmit,
    reset,
    setValue,
    watch,
    formState: { errors },
  } = useForm<
    CreateSupplierFormInput | UpdateSupplierFormInput,
    undefined,
    CreateSupplierFormValues | UpdateSupplierFormValues
  >({
    resolver: zodResolver(
      isEditMode ? updateSupplierSchema : createSupplierSchema
    ),
    defaultValues: {
      name: "",
      tax_id: "",
      email: "",
      phone: "",
      address: "",
      is_active: true,
    },
  });

  const isActive = watch("is_active");

  useEffect(() => {
    if (isEditMode && initialData) {
      reset({
        name: initialData.name ?? "",
        tax_id: initialData.tax_id ?? "",
        email: initialData.email ?? "",
        phone: initialData.phone ?? "",
        address: initialData.address ?? "",
        is_active: initialData.is_active,
      });
      return;
    }

    reset({
      name: "",
      tax_id: "",
      email: "",
      phone: "",
      address: "",
      is_active: true,
    });
  }, [isEditMode, initialData, reset]);

  const onSubmit = async (
    data: CreateSupplierFormValues | UpdateSupplierFormValues
  ) => {
    try {
      const payload = {
        name: data.name,
        tax_id: data.tax_id?.trim() || null,
        email: data.email?.trim() || null,
        phone: data.phone?.trim() || null,
        address: data.address?.trim() || null,
        is_active: data.is_active ?? true,
        created_at: initialData?.created_at || new Date().toISOString(),
        updated_at: new Date().toISOString(),
      };

      if (isEditMode && initialData) {
        await updateSupplier.mutateAsync({
          supplierId: initialData.id,
          data: payload,
        });

        toast.success("Proveedor actualizado correctamente", {
          position: "top-right",
          duration: 4000,
        });

        onSuccess?.();
        return;
      }

      await createSupplier.mutateAsync(payload);

      toast.success("Proveedor creado correctamente", {
        position: "top-right",
        duration: 4000,
      });

      reset({
        name: "",
        tax_id: "",
        email: "",
        phone: "",
        address: "",
        is_active: true,
      });

      onSuccess?.();
    } catch (error) {
      toast.error(
        error instanceof Error
          ? error.message
          : isEditMode
            ? "No se pudo actualizar el proveedor"
            : "No se pudo crear el proveedor",
        {
          position: "top-right",
          duration: 4000,
        }
      );
    }
  };

  const isPending = createSupplier.isPending || updateSupplier.isPending;

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-5 sm:space-y-6">
      <div className="grid gap-4 md:grid-cols-2">
        <div className="space-y-1.5">
          <label htmlFor="name" className="text-sm font-medium">
            Nombre
          </label>
          <Input
            id="name"
            {...register("name")}
            placeholder="Nombre del proveedor"
          />
          {errors.name && (
            <p className="text-sm text-destructive">{errors.name.message}</p>
          )}
        </div>

        <div className="space-y-1.5">
          <label htmlFor="tax_id" className="text-sm font-medium">
            CUIT
          </label>
          <Input
            id="tax_id"
            {...register("tax_id")}
            placeholder="Opcional"
          />
          {errors.tax_id && (
            <p className="text-sm text-destructive">{errors.tax_id.message}</p>
          )}
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <div className="space-y-1.5">
          <label htmlFor="email" className="text-sm font-medium">
            Email
          </label>
          <Input
            id="email"
            type="email"
            {...register("email")}
            placeholder="mail@empresa.com"
          />
          {errors.email && (
            <p className="text-sm text-destructive">{errors.email.message}</p>
          )}
        </div>

        <div className="space-y-1.5">
          <label htmlFor="phone" className="text-sm font-medium">
            Teléfono
          </label>
          <Input
            id="phone"
            {...register("phone")}
            placeholder="Opcional"
          />
          {errors.phone && (
            <p className="text-sm text-destructive">{errors.phone.message}</p>
          )}
        </div>
      </div>

      <div className="space-y-1.5">
        <label htmlFor="address" className="text-sm font-medium">
          Dirección
        </label>
        <Textarea
          id="address"
          {...register("address")}
          placeholder="Opcional"
          rows={3}
        />
        {errors.address && (
          <p className="text-sm text-destructive">{errors.address.message}</p>
        )}
      </div>

      <div className="flex flex-col gap-3 rounded-2xl border p-4 sm:gap-4 sm:p-5">
        <label className="flex items-center gap-3 text-sm font-medium">
          <Checkbox
            checked={!!isActive}
            onCheckedChange={(checked) =>
                setValue("is_active", checked === true, { shouldValidate: true })
            }
            />
          Proveedor activo
        </label>
      </div>

      <div className="flex justify-end">
        <Button type="submit" disabled={isPending} className="w-full sm:w-auto">
          {isPending
            ? isEditMode
              ? "Guardando..."
              : "Creando..."
            : isEditMode
              ? "Guardar cambios"
              : "Crear proveedor"}
        </Button>
      </div>
    </form>
  );
}