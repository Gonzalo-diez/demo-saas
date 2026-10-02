"use client";

import { useFieldArray, useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { toast } from "sonner";
import { Plus, Trash2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Checkbox } from "@/components/ui/checkbox";
import { Textarea } from "@/components/ui/textarea";

import {
  createClientSchema,
  updateClientSchema,
  type CreateClientFormInput,
  type CreateClientFormValues,
  type UpdateClientFormInput,
  type UpdateClientFormValues,
} from "@/features/admin/clients/schemas/client-schema";
import { useCreateClient } from "@/features/admin/clients/hooks/use-create-client";
import { useUpdateClient } from "@/features/admin/clients/hooks/use-update-client";
import type { Client } from "@/features/admin/clients/types";

type Props = {
  mode?: "create" | "edit";
  initialData?: Client;
  onSuccess?: () => void;
};

const createDefaultValues: CreateClientFormInput = {
  name: "",
  email: "",
  phone: "",
  tax_id: "",
  client_type: "company",
  is_active: true,
  password: "",
  branches: [
    {
      name: "Principal",
      address: "",
      city: "",
      lat: null,
      lng: null,
      contact_name: "",
      contact_phone: "",
      reference: "",
      is_main: true,
      is_active: true,
    },
  ],
};

export function CreateClientForm({
  mode = "create",
  initialData,
  onSuccess,
}: Props) {
  const createClient = useCreateClient();
  const updateClient = useUpdateClient();

  const createForm = useForm<
    CreateClientFormInput,
    undefined,
    CreateClientFormValues
  >({
    resolver: zodResolver(createClientSchema),
    defaultValues: createDefaultValues,
  });

  const updateForm = useForm<
    UpdateClientFormInput,
    undefined,
    UpdateClientFormValues
  >({
    resolver: zodResolver(updateClientSchema),
    defaultValues:
      mode === "edit" && initialData
        ? {
            name: initialData.name,
            tax_id: initialData.tax_id ?? "",
            email: initialData.email ?? "",
            phone: initialData.phone ?? "",
            is_active: initialData.is_active,
          }
        : {
            name: "",
            email: "",
            phone: "",
            tax_id: "",
            is_active: true,
          },
  });

  const isCreateMode = mode === "create";

  const createFieldArray = useFieldArray({
    control: createForm.control,
    name: "branches",
  });

  const branches = createForm.watch("branches");
  const clientIsActiveCreate = createForm.watch("is_active");
  const clientIsActiveUpdate = updateForm.watch("is_active");

  function setMain(index: number) {
    branches.forEach((_, i) => {
      createForm.setValue(`branches.${i}.is_main`, i === index, {
        shouldDirty: true,
        shouldValidate: true,
      });
    });
  }

  async function onSubmitCreate(data: CreateClientFormValues) {
    try {
      await createClient.mutateAsync({
        name: data.name,
        tax_id: data.tax_id || null,
        email: data.email || null,
        phone: data.phone || null,
        client_type: data.client_type,
        is_active: data.is_active,
        password: data.password,
        branches: data.branches.map((branch) => ({
          name: branch.name,
          address: branch.address || null,
          city: branch.city || null,
          lat: branch.lat ?? null,
          lng: branch.lng ?? null,
          contact_name: branch.contact_name || null,
          contact_phone: branch.contact_phone || null,
          reference: branch.reference || null,
          is_main: branch.is_main,
          is_active: branch.is_active,
        })),
      });

      toast.success("Cliente creado");
      createForm.reset(createDefaultValues);
      onSuccess?.();
    } catch (error) {
      toast.error(
        error instanceof Error ? error.message : "Error al crear el cliente",
      );
    }
  }

  async function onSubmitUpdate(data: UpdateClientFormValues) {
    if (!initialData) return;

    try {
      await updateClient.mutateAsync({
        clientId: initialData.id,
        data: {
          name: data.name,
          tax_id: data.tax_id || null,
          email: data.email || null,
          phone: data.phone || null,
          is_active: data.is_active,
          // Solo se manda si el admin completó el campo; vacío = no tocar
          // la contraseña actual del cliente.
          password: data.password || null,
        },
      });

      toast.success("Cliente actualizado");
      onSuccess?.();
    } catch (error) {
      toast.error(
        error instanceof Error
          ? error.message
          : "Error al actualizar el cliente",
      );
    }
  }

  if (!isCreateMode) {
    const {
      register,
      handleSubmit,
      formState: { errors },
      setValue,
    } = updateForm;

    return (
      <form
        onSubmit={handleSubmit(onSubmitUpdate)}
        className="space-y-5 sm:space-y-6"
      >
        <div className="space-y-4 rounded-2xl border p-4 sm:p-5">
          <h4 className="text-sm font-semibold">Datos del cliente</h4>

          <div className="space-y-1.5">
            <label className="text-sm font-medium">Nombre</label>
            <Input {...register("name")} />
            {errors.name && (
              <p className="text-sm text-destructive">{errors.name.message}</p>
            )}
          </div>

          <div className="space-y-1.5">
            <label className="text-sm font-medium">CUIT</label>
            <Input {...register("tax_id")} />
            {errors.tax_id && (
              <p className="text-sm text-destructive">
                {errors.tax_id.message}
              </p>
            )}
          </div>

          <div className="space-y-1.5">
            <label className="text-sm font-medium">Email</label>
            <Input type="email" {...register("email")} />
            {errors.email && (
              <p className="text-sm text-destructive">
                {errors.email.message}
              </p>
            )}
          </div>

          <div className="space-y-1.5">
            <label className="text-sm font-medium">Teléfono</label>
            <Input {...register("phone")} />
            {errors.phone && (
              <p className="text-sm text-destructive">
                {errors.phone.message}
              </p>
            )}
          </div>

          <div className="space-y-1.5">
            <label className="text-sm font-medium">
              Nueva contraseña (opcional)
            </label>
            <Input type="password" autoComplete="new-password" {...register("password")} />
            <p className="text-xs text-muted-foreground">
              Dejalo vacío para no cambiar la contraseña actual del cliente.
            </p>
            {errors.password && (
              <p className="text-sm text-destructive">
                {errors.password.message}
              </p>
            )}
          </div>

          <div className="flex items-center gap-2 pt-2">
            <Checkbox
              checked={clientIsActiveUpdate}
              onCheckedChange={(checked) =>
                setValue("is_active", checked === true, {
                  shouldDirty: true,
                  shouldValidate: true,
                })
              }
            />
            <label className="text-sm">Cliente activo</label>
          </div>
        </div>

        <div className="flex justify-end">
          <Button
            type="submit"
            disabled={updateClient.isPending}
            className="w-full sm:w-auto"
          >
            {updateClient.isPending ? "Guardando..." : "Guardar cambios"}
          </Button>
        </div>
      </form>
    );
  }

  const {
    register,
    handleSubmit,
    formState: { errors },
    setValue,
  } = createForm;

  return (
    <form
      onSubmit={handleSubmit(onSubmitCreate)}
      className="space-y-5 sm:space-y-6"
    >
      <div className="space-y-4 rounded-2xl border p-4 sm:p-5">
        <h4 className="text-sm font-semibold">Datos del cliente</h4>

        <div className="space-y-1.5">
          <label className="text-sm font-medium">Nombre</label>
          <Input {...register("name")} />
          {errors.name && (
            <p className="text-sm text-destructive">{errors.name.message}</p>
          )}
        </div>

        <div className="grid gap-4 md:grid-cols-2">
          <div className="space-y-1.5">
            <label className="text-sm font-medium">CUIT</label>
            <Input {...register("tax_id")} />
            {errors.tax_id && (
              <p className="text-sm text-destructive">
                {errors.tax_id.message}
              </p>
            )}
          </div>

          <div className="space-y-1.5">
            <label className="text-sm font-medium">Tipo</label>
            <Input {...register("client_type")} />
            {errors.client_type && (
              <p className="text-sm text-destructive">
                {errors.client_type.message}
              </p>
            )}
          </div>

          <div className="space-y-1.5">
            <label className="text-sm font-medium">Email</label>
            <Input type="email" {...register("email")} />
            {errors.email && (
              <p className="text-sm text-destructive">
                {errors.email.message}
              </p>
            )}
          </div>

          <div className="space-y-1.5">
            <label className="text-sm font-medium">Teléfono</label>
            <Input {...register("phone")} />
            {errors.phone && (
              <p className="text-sm text-destructive">
                {errors.phone.message}
              </p>
            )}
          </div>

          <div className="space-y-1.5 md:col-span-2">
            <label className="text-sm font-medium">Contraseña</label>
            <Input type="password" autoComplete="new-password" {...register("password")} />
            <p className="text-xs text-muted-foreground">
              El cliente la usa para entrar a la tienda online.
            </p>
            {errors.password && (
              <p className="text-sm text-destructive">
                {errors.password.message}
              </p>
            )}
          </div>
        </div>

        <div className="flex items-center gap-2 pt-2">
          <Checkbox
            checked={clientIsActiveCreate}
            onCheckedChange={(checked) =>
              setValue("is_active", checked === true, {
                shouldDirty: true,
                shouldValidate: true,
              })
            }
          />
          <label className="text-sm">Cliente activo</label>
        </div>
      </div>

      <div className="space-y-4 rounded-2xl border p-4 sm:p-5">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <h4 className="text-sm font-semibold">Sucursales</h4>

          <Button
            type="button"
            variant="outline"
            className="w-full sm:w-auto"
            onClick={() =>
              createFieldArray.append({
                name: "",
                address: "",
                city: "",
                lat: null,
                lng: null,
                contact_name: "",
                contact_phone: "",
                reference: "",
                is_main: false,
                is_active: true,
              })
            }
          >
            <Plus className="mr-2 h-4 w-4" />
            Agregar
          </Button>
        </div>

        {createFieldArray.fields.map((field, index) => (
          <div key={field.id} className="space-y-4 rounded-xl border p-4">
            <div className="flex items-center justify-between gap-3">
              <p className="text-sm font-medium">Sucursal {index + 1}</p>

              <Button
                type="button"
                variant="ghost"
                size="icon"
                onClick={() => createFieldArray.remove(index)}
                disabled={createFieldArray.fields.length === 1}
              >
                <Trash2 className="h-4 w-4" />
              </Button>
            </div>

            <div className="space-y-1.5">
              <label className="text-sm">Nombre</label>
              <Input {...register(`branches.${index}.name`)} />
              {errors.branches?.[index]?.name && (
                <p className="text-sm text-destructive">
                  {errors.branches[index]?.name?.message}
                </p>
              )}
            </div>

            <div className="space-y-1.5">
              <label className="text-sm">Dirección</label>
              <Textarea {...register(`branches.${index}.address`)} rows={2} />
            </div>

            <div className="space-y-1.5">
              <label className="text-sm">Ciudad</label>
              <Input {...register(`branches.${index}.city`)} />
            </div>

            <div className="grid gap-3 sm:grid-cols-2">
              <div className="space-y-1.5">
                <label className="text-sm">Latitud</label>
                <Input
                  type="number"
                  step="any"
                  {...register(`branches.${index}.lat`)}
                />
                {errors.branches?.[index]?.lat && (
                  <p className="text-sm text-destructive">
                    {errors.branches[index]?.lat?.message}
                  </p>
                )}
              </div>

              <div className="space-y-1.5">
                <label className="text-sm">Longitud</label>
                <Input
                  type="number"
                  step="any"
                  {...register(`branches.${index}.lng`)}
                />
                {errors.branches?.[index]?.lng && (
                  <p className="text-sm text-destructive">
                    {errors.branches[index]?.lng?.message}
                  </p>
                )}
              </div>
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-1.5">
                <label className="text-sm">Contacto</label>
                <Input {...register(`branches.${index}.contact_name`)} />
              </div>

              <div className="space-y-1.5">
                <label className="text-sm">Teléfono contacto</label>
                <Input {...register(`branches.${index}.contact_phone`)} />
              </div>
            </div>

            <div className="space-y-1.5">
              <label className="text-sm">Referencia</label>
              <Input {...register(`branches.${index}.reference`)} />
            </div>

            <div className="flex flex-col gap-3 pt-2 sm:flex-row sm:flex-wrap sm:items-center sm:gap-6">
              <div className="flex items-center gap-2">
                <Checkbox
                  checked={branches[index]?.is_main ?? false}
                  onCheckedChange={() => setMain(index)}
                />
                <label className="text-sm">Sucursal principal</label>
              </div>

              <div className="flex items-center gap-2">
                <Checkbox
                  checked={branches[index]?.is_active ?? true}
                  onCheckedChange={(checked) =>
                    createForm.setValue(
                      `branches.${index}.is_active`,
                      checked === true,
                      {
                        shouldDirty: true,
                        shouldValidate: true,
                      },
                    )
                  }
                />
                <label className="text-sm">Activa</label>
              </div>
            </div>
          </div>
        ))}

        {errors.branches?.root?.message ? (
          <p className="text-sm text-destructive">
            {errors.branches.root.message}
          </p>
        ) : null}

        {typeof errors.branches?.message === "string" ? (
          <p className="text-sm text-destructive">{errors.branches.message}</p>
        ) : null}
      </div>

      <div className="flex justify-end">
        <Button
          type="submit"
          disabled={createClient.isPending}
          className="w-full sm:w-auto"
        >
          {createClient.isPending ? "Guardando..." : "Crear cliente"}
        </Button>
      </div>
    </form>
  );
}