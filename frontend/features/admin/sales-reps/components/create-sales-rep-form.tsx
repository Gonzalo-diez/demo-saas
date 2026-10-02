"use client";

import { useEffect } from "react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import { zodResolver } from "@hookform/resolvers/zod";

import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";

import {
  createSalesRepSchema,
  updateSalesRepSchema,
  type CreateSalesRepFormInput,
  type CreateSalesRepFormValues,
  type UpdateSalesRepFormInput,
  type UpdateSalesRepFormValues,
} from "@/features/admin/sales-reps/schemas/sales-rep-schema";
import { useCreateSalesRep } from "@/features/admin/sales-reps/hooks/use-create-sales-rep";
import { useUpdateSalesRep } from "@/features/admin/sales-reps/hooks/use-update-sales-rep";
import type { SalesRep } from "@/features/admin/sales-reps/types";

type CreateSalesRepFormProps = {
  onSuccess?: () => void;
  mode?: "create" | "edit";
  initialData?: SalesRep | null;
};

export function CreateSalesRepForm({
  onSuccess,
  mode = "create",
  initialData = null,
}: CreateSalesRepFormProps) {
  const createSalesRep = useCreateSalesRep();
  const updateSalesRep = useUpdateSalesRep();

  const isEditMode = mode === "edit";

  const {
    register,
    handleSubmit,
    reset,
    setValue,
    watch,
    formState: { errors },
  } = useForm<
    CreateSalesRepFormInput | UpdateSalesRepFormInput,
    undefined,
    CreateSalesRepFormValues | UpdateSalesRepFormValues
  >({
    resolver: zodResolver(isEditMode ? updateSalesRepSchema : createSalesRepSchema),
    defaultValues: {
      name: "",
      email: "",
      phone: "",
      home_lat: "",
      home_lng: "",
      coverage_radius_km: "",
      password: "",
      is_active: true,
      is_superuser: false,
    },
  });

  const isActive = watch("is_active");
  const isSuperuser = watch("is_superuser");

  useEffect(() => {
    if (isEditMode && initialData) {
      reset({
        name: initialData.name ?? "",
        email: initialData.email ?? "",
        phone: initialData.phone ?? "",
        home_lat: initialData.home_lat ?? "",
        home_lng: initialData.home_lng ?? "",
        coverage_radius_km: initialData.coverage_radius_km ?? "",
        password: "",
        is_active: initialData.is_active,
        is_superuser: initialData.is_superuser,
      });
      return;
    }

    reset({
      name: "",
      email: "",
      phone: "",
      home_lat: "",
      home_lng: "",
      coverage_radius_km: "",
      password: "",
      is_active: true,
      is_superuser: false,
    });
  }, [isEditMode, initialData, reset]);

  const onSubmit = async (
    data: CreateSalesRepFormValues | UpdateSalesRepFormValues
  ) => {
    try {
      if (isEditMode && initialData) {
        const payload = {
          name: data.name,
          email: data.email,
          phone: data.phone || null,
          home_lat: data.home_lat,
          home_lng: data.home_lng,
          coverage_radius_km: data.coverage_radius_km,
          is_active: data.is_active,
          is_superuser: data.is_superuser,
          ...(data.password ? { password: data.password } : {}),
        };

        await updateSalesRep.mutateAsync({
          salesRepId: initialData.id,
          data: payload,
        });

        toast.success("Vendedor actualizado correctamente", {
          position: "top-right",
          duration: 4000,
        });

        onSuccess?.();
        return;
      }

      await createSalesRep.mutateAsync({
        name: data.name,
        email: data.email,
        phone: data.phone || null,
        home_lat: data.home_lat,
        home_lng: data.home_lng,
        coverage_radius_km: data.coverage_radius_km,
        password: data.password!,
        is_active: data.is_active,
        is_superuser: data.is_superuser,
      });

      toast.success("Vendedor creado correctamente", {
        position: "top-right",
        duration: 4000,
      });

      reset();
      onSuccess?.();
    } catch (error) {
      toast.error(
        error instanceof Error
          ? error.message
          : isEditMode
            ? "No se pudo actualizar el vendedor"
            : "No se pudo crear el vendedor",
        {
          position: "top-right",
          duration: 4000,
        }
      );
    }
  };

  const isPending = createSalesRep.isPending || updateSalesRep.isPending;

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-5 sm:space-y-6">
      <div className="grid gap-4 md:grid-cols-2">
        <div className="space-y-1.5">
          <label htmlFor="name" className="text-sm font-medium">
            Nombre
          </label>
          <Input id="name" {...register("name")} placeholder="Nombre del vendedor" />
          {errors.name && (
            <p className="text-sm text-destructive">{errors.name.message}</p>
          )}
        </div>

        <div className="space-y-1.5">
          <label htmlFor="email" className="text-sm font-medium">
            Email
          </label>
          <Input id="email" type="email" {...register("email")} placeholder="mail@empresa.com" />
          {errors.email && (
            <p className="text-sm text-destructive">{errors.email.message}</p>
          )}
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <div className="space-y-1.5">
          <label htmlFor="phone" className="text-sm font-medium">
            Teléfono
          </label>
          <Input id="phone" {...register("phone")} placeholder="Opcional" />
          {errors.phone && (
            <p className="text-sm text-destructive">{errors.phone.message}</p>
          )}
        </div>

        <div className="space-y-1.5">
          <label htmlFor="password" className="text-sm font-medium">
            {isEditMode ? "Nueva contraseña" : "Contraseña"}
          </label>
          <Input
            id="password"
            type="password"
            {...register("password")}
            placeholder={isEditMode ? "Dejar vacío para no cambiarla" : "Mínimo 6 caracteres"}
          />
          {errors.password && (
            <p className="text-sm text-destructive">{errors.password.message}</p>
          )}
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <div className="space-y-1.5">
          <label htmlFor="home_lat" className="text-sm font-medium">
            Latitud (base)
          </label>
          <Input
            id="home_lat"
            {...register("home_lat")}
            placeholder="-34.6037"
          />
          {errors.home_lat && (
            <p className="text-sm text-destructive">{errors.home_lat.message}</p>
          )}
        </div>

        <div className="space-y-1.5">
          <label htmlFor="home_lng" className="text-sm font-medium">
            Longitud (base)
          </label>
          <Input
            id="home_lng"
            {...register("home_lng")}
            placeholder="-58.3816"
          />
          {errors.home_lng && (
            <p className="text-sm text-destructive">{errors.home_lng.message}</p>
          )}
        </div>

        <div className="space-y-1.5">
          <label htmlFor="coverage_radius_km" className="text-sm font-medium">
            Radio de cobertura (km)
          </label>
          <Input
            id="coverage_radius_km"
            {...register("coverage_radius_km")}
            placeholder="25"
          />
          {errors.coverage_radius_km && (
            <p className="text-sm text-destructive">
              {errors.coverage_radius_km.message}
            </p>
          )}
        </div>
      </div>

      <div className="flex flex-col gap-3 rounded-2xl border p-4 sm:gap-4 sm:p-5">
        <label className="flex items-center gap-3 text-sm font-medium">
          <Checkbox
            checked={isActive}
            onCheckedChange={(checked) => setValue("is_active", checked === true)}
          />
          Vendedor activo
        </label>

        <label className="flex items-center gap-3 text-sm font-medium">
          <Checkbox
            checked={isSuperuser}
            onCheckedChange={(checked) => setValue("is_superuser", checked === true)}
          />
          Es superusuario
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
              : "Crear vendedor"}
        </Button>
      </div>
    </form>
  );
}