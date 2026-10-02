"use client";

import { useEffect, useMemo } from "react";
import { useFieldArray, useForm, useWatch } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Plus, Trash2 } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

import {
  createOrderB2BSchema,
  type CreateOrderB2BFormValues,
} from "@/features/admin/orders/schemas/order-schema";
import { useCreateOrderB2B } from "@/features/admin/orders/hooks/use-create-order";
import { useClients } from "@/features/admin/clients/hooks/use-clients";
import { useProducts } from "@/features/admin/products/hooks/use-products";
import type { ClientBranch } from "@/features/admin/clients/types";

type CreateOrderFormProps = {
  onSuccess?: () => void;
};

type OrderFormItem = {
  product_id: number;
  quantity: number;
};

function formatCurrency(value: number) {
  return new Intl.NumberFormat("es-AR", {
    style: "currency",
    currency: "ARS",
    maximumFractionDigits: 2,
  }).format(Number.isNaN(value) ? 0 : value);
}

export function CreateOrderForm({ onSuccess }: CreateOrderFormProps) {
  const createOrderMutation = useCreateOrderB2B();

  const clientsQuery = useClients({
    page: 1,
    page_size: 20,
    search: "",
    status: "active",
    sort: "name",
  });

  const productsQuery = useProducts({
    page: 1,
    page_size: 20,
    search: "",
    status: "active",
    brand: "",
    sort: "name-asc",
  });

  const {
    handleSubmit,
    control,
    register,
    setValue,
    reset,
    formState: { errors },
  } = useForm<CreateOrderB2BFormValues>({
    resolver: zodResolver(createOrderB2BSchema),
    defaultValues: {
      client_id: undefined,
      client_branch_id: null,
      items: [{ product_id: 0, quantity: 1 }],
    },
  });

  const { fields, append, remove } = useFieldArray({
    control,
    name: "items",
  });

  const watchedClientId = useWatch({
    control,
    name: "client_id",
  });

  const watchedBranchId = useWatch({
    control,
    name: "client_branch_id",
  });

  const watchedDocumentType = useWatch({
    control,
    name: "document_type",
  });

  const watchedItems = useWatch({
    control,
    name: "items",
  });

  const clientId = Number(watchedClientId ?? 0);
  const branchId =
    watchedBranchId === null || watchedBranchId === undefined
      ? null
      : Number(watchedBranchId);
  const items = (watchedItems ?? []) as OrderFormItem[];

  const clients = clientsQuery.data?.clients ?? [];
  const products = productsQuery.data?.items ?? [];

  const selectedClient =
    clients.find((client) => client.id === clientId) ?? null;

  const availableBranches = useMemo<ClientBranch[]>(() => {
    return (selectedClient?.branches ?? []).filter(
      (branch) => branch.is_active,
    );
  }, [selectedClient]);

  useEffect(() => {
    if (!selectedClient) {
      if (branchId !== null) {
        setValue("client_branch_id", null, {
          shouldValidate: true,
          shouldDirty: true,
        });
      }
      return;
    }

    const branchStillExists = availableBranches.some(
      (branch) => branch.id === branchId,
    );

    if (branchStillExists) {
      return;
    }

    if (availableBranches.length === 1) {
      setValue("client_branch_id", availableBranches[0].id, {
        shouldValidate: true,
        shouldDirty: true,
      });
      return;
    }

    const mainBranch = availableBranches.find((branch) => branch.is_main);
    setValue("client_branch_id", mainBranch?.id ?? null, {
      shouldValidate: true,
      shouldDirty: true,
    });
  }, [selectedClient, availableBranches, branchId, setValue]);

  const enrichedItems = useMemo(() => {
    return items.map((item) => {
      const product = products.find((p) => p.id === Number(item.product_id));
      const unitCost = Number(product?.unit_cost ?? 0);
      const unitPrice = Number(product?.unit_price ?? 0);
      const quantity = Number(item.quantity ?? 0);

      const subtotalCost = unitCost * quantity;
      const subtotal = unitPrice * quantity;
      const marginAmount = subtotal - subtotalCost;

      return {
        ...item,
        product,
        unitCost,
        unitPrice,
        subtotalCost,
        subtotal,
        marginAmount,
      };
    });
  }, [items, products]);

  const totals = useMemo(() => {
    return enrichedItems.reduce(
      (acc, item) => {
        acc.totalCost += item.subtotalCost;
        acc.totalSale += item.subtotal;
        acc.totalMargin += item.marginAmount;
        return acc;
      },
      {
        totalCost: 0,
        totalSale: 0,
        totalMargin: 0,
      },
    );
  }, [enrichedItems]);

  async function onSubmit(data: CreateOrderB2BFormValues) {
    if (
      enrichedItems.some(
        (item) => item.quantity > (item.product?.stock_current ?? 0),
      )
    ) {
      toast.error("Hay productos sin stock suficiente");
      return;
    }

    try {
      // Usar la propiedad del objeto devuelto por el hook
      await createOrderMutation.mutateAsync({
        client_id: data.client_id,
        client_branch_id: data.client_branch_id ?? null,
        document_type: data.document_type,
        items: data.items.map((item) => ({
          product_id: item.product_id,
          quantity: item.quantity,
        })),
      });

      reset({
        client_id: 0,
        client_branch_id: null,
        document_type: undefined,
        items: [{ product_id: 0, quantity: 1 }],
      });

      onSuccess?.();
    } catch (error) {
      console.error("Error creating order:", error);
    }
  }

  const isPending =
    createOrderMutation.isPending ||
    clientsQuery.isLoading ||
    productsQuery.isLoading;

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-5 sm:space-y-6">
      <section className="space-y-4 rounded-2xl border p-4">
        <div className="space-y-1">
          <h4 className="text-sm font-semibold">Datos de la orden</h4>
          <p className="text-xs text-muted-foreground">
            Seleccioná el cliente, la sucursal y agregá observaciones si hace
            falta.
          </p>
        </div>

        <div className="space-y-1.5">
          <label className="text-sm font-medium">Cliente</label>
          <Select
            value={clientId > 0 ? String(clientId) : "__empty__"}
            onValueChange={(value) => {
              setValue("client_id", value === "__empty__" ? 0 : Number(value), {
                shouldValidate: true,
                shouldDirty: true,
              });
              setValue("client_branch_id", null, {
                shouldValidate: true,
                shouldDirty: true,
              });
            }}
          >
            <SelectTrigger>
              <SelectValue placeholder="Seleccionar cliente" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="__empty__" disabled>
                Seleccionar cliente
              </SelectItem>

              {clients.map((client) => (
                <SelectItem key={client.id} value={String(client.id)}>
                  {client.name}{" "}
                  {client.sales_rep_id ? `- ${client.sales_rep_id}` : ""}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          {errors.client_id && (
            <p className="text-sm text-destructive">
              {errors.client_id.message}
            </p>
          )}
        </div>

        <div className="space-y-1.5">
          <label className="text-sm font-medium">Sucursal</label>
          <Select
            value={branchId ? String(branchId) : "__empty__"}
            onValueChange={(value) =>
              setValue(
                "client_branch_id",
                value === "__empty__" ? null : Number(value),
                {
                  shouldValidate: true,
                  shouldDirty: true,
                },
              )
            }
            disabled={!selectedClient || availableBranches.length === 0}
          >
            <SelectTrigger>
              <SelectValue
                placeholder={
                  !selectedClient
                    ? "Primero seleccioná un cliente"
                    : availableBranches.length === 0
                      ? "El cliente no tiene sucursales activas"
                      : "Seleccionar sucursal"
                }
              />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="__empty__" disabled>
                Seleccionar sucursal
              </SelectItem>

              {availableBranches.map((branch) => (
                <SelectItem key={branch.id} value={String(branch.id)}>
                  {branch.name}
                  {branch.city ? ` - ${branch.city}` : ""}
                  {branch.is_main ? " (Principal)" : ""}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          {errors.client_branch_id && (
            <p className="text-sm text-destructive">
              {errors.client_branch_id.message}
            </p>
          )}
        </div>

        <div className="space-y-1.5">
          <label className="text-sm font-medium">Tipo de documento</label>

          <Select
            value={watchedDocumentType ?? ""}
            onValueChange={(value) =>
              setValue(
                "document_type",
                value as "sales_invoice" | "sales_quote",
                {
                  shouldValidate: true,
                  shouldDirty: true,
                },
              )
            }
          >
            <SelectTrigger>
              <SelectValue placeholder="Seleccionar tipo de documento" />
            </SelectTrigger>

            <SelectContent>
              <SelectItem value="sales_invoice">Remito</SelectItem>

              <SelectItem value="sales_quote">Presupuesto</SelectItem>
            </SelectContent>
          </Select>

          {errors.document_type && (
            <p className="text-sm text-destructive">
              {errors.document_type.message}
            </p>
          )}
        </div>
      </section>

      <section className="space-y-4 rounded-2xl border p-4">
        <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
          <div className="space-y-1">
            <h4 className="text-sm font-semibold">Productos</h4>
            <p className="text-xs text-muted-foreground">
              Sumá uno o más productos con su cantidad.
            </p>
          </div>

          <Button
            type="button"
            variant="outline"
            className="w-full sm:w-auto"
            onClick={() => append({ product_id: 0, quantity: 1 })}
            disabled={products.length === 0}
          >
            <Plus className="mr-2 h-4 w-4" />
            Agregar producto
          </Button>
        </div>

        <div className="space-y-4">
          {fields.map((field, index) => {
            const currentItem = enrichedItems[index];
            const currentProduct = currentItem?.product;
            const currentStock = currentProduct?.stock_current ?? 0;
            const currentQuantity = Number(items[index]?.quantity ?? 0);
            const exceedsStock =
              currentProduct != null && currentQuantity > currentStock;

            return (
              <div
                key={field.id}
                className="grid gap-3 rounded-2xl border p-4 sm:p-5 md:grid-cols-12"
              >
                <div className="space-y-1.5 md:col-span-4">
                  <label className="text-sm font-medium">Producto</label>
                  <Select
                    value={
                      Number(items[index]?.product_id) > 0
                        ? String(items[index]?.product_id)
                        : "__empty__"
                    }
                    onValueChange={(value) =>
                      setValue(
                        `items.${index}.product_id`,
                        value === "__empty__" ? 0 : Number(value),
                        {
                          shouldValidate: true,
                          shouldDirty: true,
                        },
                      )
                    }
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Seleccionar producto" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="__empty__" disabled>
                        Seleccionar producto
                      </SelectItem>

                      {products.map((product) => (
                        <SelectItem key={product.id} value={String(product.id)}>
                          {product.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  {errors.items?.[index]?.product_id && (
                    <p className="text-sm text-destructive">
                      {errors.items[index]?.product_id?.message}
                    </p>
                  )}
                </div>

                <div className="space-y-1.5 md:col-span-2">
                  <label className="text-sm font-medium">Cantidad</label>
                  <Input
                    type="number"
                    min="1"
                    {...register(`items.${index}.quantity`, {
                      valueAsNumber: true,
                    })}
                  />
                  {errors.items?.[index]?.quantity && (
                    <p className="text-sm text-destructive">
                      {errors.items[index]?.quantity?.message}
                    </p>
                  )}
                </div>

                <div className="space-y-1.5 md:col-span-2">
                  <label className="text-sm font-medium">Stock</label>
                  <div className="rounded-md border bg-muted/40 px-3 py-2 text-sm">
                    {currentProduct ? currentStock : "-"}
                  </div>
                  {exceedsStock && (
                    <p className="text-sm text-destructive">
                      La cantidad supera el stock disponible.
                    </p>
                  )}
                </div>

                <div className="space-y-1.5 md:col-span-3">
                  <label className="text-sm font-medium">Subtotal</label>
                  <div className="rounded-md border bg-muted/40 px-3 py-2 text-sm">
                    {currentProduct
                      ? formatCurrency(currentItem.subtotal)
                      : "-"}
                  </div>
                </div>

                <div className="flex items-end md:col-span-1">
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon"
                    onClick={() => remove(index)}
                    disabled={fields.length === 1}
                    className="w-full md:w-auto"
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            );
          })}
        </div>

        {errors.items && !Array.isArray(errors.items) && (
          <p className="text-sm text-destructive">{errors.items.message}</p>
        )}
      </section>

      <section className="grid gap-4 rounded-2xl border p-4 sm:p-5 md:grid-cols-3">
        <div className="space-y-1">
          <p className="text-xs text-muted-foreground">Costo total</p>
          <p className="text-lg font-semibold">
            {formatCurrency(totals.totalCost)}
          </p>
        </div>
        <div className="space-y-1">
          <p className="text-xs text-muted-foreground">Venta total</p>
          <p className="text-lg font-semibold">
            {formatCurrency(totals.totalSale)}
          </p>
        </div>
        <div className="space-y-1">
          <p className="text-xs text-muted-foreground">Margen total</p>
          <p className="text-lg font-semibold">
            {formatCurrency(totals.totalMargin)}
          </p>
        </div>
      </section>

      <div className="flex justify-end">
        <Button type="submit" disabled={isPending} className="w-full sm:w-auto">
          {createOrderMutation.isPending ? "Creando..." : "Crear orden"}
        </Button>
      </div>
    </form>
  );
}
