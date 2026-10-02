"use client";

import { useEffect, useMemo } from "react";
import { useFieldArray, useForm, useWatch } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { toast } from "sonner";
import { Plus, Trash2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

import {
  createSalesInvoiceSchema,
  type CreateSalesInvoiceFormInput,
  type CreateSalesInvoiceFormValues,
} from "@/features/admin/sales-invoices/schemas/sales-invoice-schema";
import { useCreateSalesInvoice } from "@/features/admin/sales-invoices/hooks/use-create-sales-invoice";
import { useClients } from "@/features/admin/clients/hooks/use-clients";
import { useProducts } from "@/features/admin/products/hooks/use-products";
import { useAdminOrders } from "@/features/admin/orders/hooks/use-orders";
import type { ClientBranch } from "@/features/admin/clients/types";

type CreateSalesInvoiceFormProps = {
  onSuccess?: () => void;
};

type SalesFormItem = {
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

export function CreateSalesInvoiceForm({
  onSuccess,
}: CreateSalesInvoiceFormProps) {
  const createSalesInvoice = useCreateSalesInvoice();

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

  const ordersQuery = useAdminOrders({
    page: 1,
    page_size: 20,
    status: "delivered",
  });

  const {
    handleSubmit,
    control,
    register,
    setValue,
    reset,
    formState: { errors },
  } = useForm<CreateSalesInvoiceFormInput, undefined, CreateSalesInvoiceFormValues>(
    {
      resolver: zodResolver(createSalesInvoiceSchema),
      defaultValues: {
        sales_type: "B2B",
        order_id: null,
        client_id: 0,
        client_branch_id: null,
        invoice_number: "",
        invoice_date: "",
        notes: "",
        items: [{ product_id: 0, product_name: "", quantity: 1 }],
      },
    }
  );

  const { fields, append, remove } = useFieldArray({
    control,
    name: "items",
  });

  const watchedOrderId = useWatch({ control, name: "order_id" });
  const watchedClientId = useWatch({ control, name: "client_id" });
  const watchedBranchId = useWatch({ control, name: "client_branch_id" });
  const watchedItems = useWatch({ control, name: "items" });
  const watchedSalesType = useWatch({ control, name: "sales_type" });

  const orderId =
    watchedOrderId === null || watchedOrderId === undefined
      ? null
      : Number(watchedOrderId);
  const clientId = Number(watchedClientId ?? 0);
  const branchId =
    watchedBranchId === null || watchedBranchId === undefined
      ? null
      : Number(watchedBranchId);
  const items = (watchedItems ?? []) as SalesFormItem[];
  const salesType = watchedSalesType ?? "B2B";

  const clients = clientsQuery.data?.clients ?? [];
  const products = productsQuery.data?.items ?? [];
  const orders = ordersQuery.data?.items ?? [];

  const selectedClient =
    clients.find((client) => client.id === clientId) ?? null;

  const selectedOrder =
    orders.find((order) => order.id === orderId) ?? null;

  const availableBranches = useMemo<ClientBranch[]>(() => {
    return (selectedClient?.branches ?? []).filter((branch) => branch.is_active);
  }, [selectedClient]);

  useEffect(() => {
    if (selectedOrder) {
      setValue("sales_type", selectedOrder.sales_type, {
        shouldValidate: true,
        shouldDirty: true,
      });

      setValue("client_id", selectedOrder.client_id, {
        shouldValidate: true,
        shouldDirty: true,
      });

      setValue("client_branch_id", selectedOrder.client_branch_id ?? null, {
        shouldValidate: true,
        shouldDirty: true,
      });

      setValue(
        "items",
        selectedOrder.items.map((item) => ({
          product_id: item.product_id,
          product_name: item.product_name_snapshot,
          quantity: item.quantity,
        })),
        {
          shouldValidate: true,
          shouldDirty: true,
        }
      );
    }
  }, [selectedOrder, setValue]);

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
      (branch) => branch.id === branchId
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
      const quantity = Number(item.quantity ?? 0);
      const unitPrice = Number(product?.unit_price ?? 0);
      const subtotal = quantity * unitPrice;

      return {
        ...item,
        product,
        quantity,
        unitPrice,
        subtotal,
      };
    });
  }, [items, products]);

  const totals = useMemo(() => {
    return enrichedItems.reduce(
      (acc, item) => {
        acc.total += item.subtotal;
        return acc;
      },
      { total: 0 }
    );
  }, [enrichedItems]);

  async function onSubmit(data: CreateSalesInvoiceFormValues) {
    try {
      await createSalesInvoice.mutateAsync({
        sales_type: data.sales_type,
        order_id: data.order_id ?? null,
        client_id: data.client_id,
        client_branch_id: data.client_branch_id ?? null,
        invoice_number: data.invoice_number,
        invoice_date: data.invoice_date,
        notes: data.notes || null,
        items: data.items.map((item) => ({
          product_id: item.product_id,
          product_name: item.product_name,
          product_brand: null,
          product_sku: null,
          quantity: item.quantity,
        })),
      });

      toast.success("Remito de venta creado correctamente", {
        position: "top-right",
        duration: 4000,
      });

      reset({
        sales_type: "B2B",
        order_id: null,
        client_id: 0,
        client_branch_id: null,
        invoice_number: "",
        invoice_date: "",
        notes: "",
        items: [{ product_id: 0, product_name: "", quantity: 1 }],
      });

      onSuccess?.();
    } catch (error) {
      toast.error(
        error instanceof Error
          ? error.message
          : "No se pudo crear el remito de venta",
        {
          position: "top-right",
          duration: 4000,
        }
      );
    }
  }

  const isPending =
    createSalesInvoice.isPending ||
    clientsQuery.isLoading ||
    productsQuery.isLoading ||
    ordersQuery.isLoading;

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
      <section className="space-y-4 rounded-2xl border p-4 sm:p-5">
        <div className="space-y-1">
          <h4 className="text-sm font-semibold">Datos del remito</h4>
          <p className="text-xs text-muted-foreground">
            Para ventas directas en la distribuidora (mostrador). Los pedidos
            hechos por la página o a través de un vendedor se cargan desde
            Pedidos y generan su remito solos.
          </p>
        </div>

        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          <div className="space-y-1.5">
            <label className="text-sm font-medium">Tipo de venta</label>
            <div className="flex h-10 items-center rounded-md border border-input bg-muted/40 px-3 text-sm">
              <span className="font-medium">{salesType === "ONLINE" ? "Online" : "B2B"}</span>
              <span className="ml-2 text-xs text-muted-foreground">
                {selectedOrder
                  ? `(heredado de la Orden #${selectedOrder.id})`
                  : "(venta directa en la distribuidora)"}
              </span>
            </div>
          </div>

          <div className="space-y-1.5">
            <label className="text-sm font-medium">Orden asociada</label>
            <Select
              value={orderId ? String(orderId) : "__empty__"}
              onValueChange={(value) =>
                setValue(
                  "order_id",
                  value === "__empty__" ? null : Number(value),
                  {
                    shouldValidate: true,
                    shouldDirty: true,
                  }
                )
              }
            >
              <SelectTrigger>
                <SelectValue placeholder="Sin orden" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="__empty__">Sin orden</SelectItem>
                {orders.map((order) => (
                  <SelectItem key={order.id} value={String(order.id)}>
                    Orden #{order.id}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            {errors.order_id && (
              <p className="text-sm text-destructive">{errors.order_id.message}</p>
            )}
          </div>

          <div className="space-y-1.5">
            <label className="text-sm font-medium">Cliente</label>
            <Select
              value={clientId > 0 ? String(clientId) : "__empty__"}
              onValueChange={(value) =>
                setValue("client_id", value === "__empty__" ? 0 : Number(value), {
                  shouldValidate: true,
                  shouldDirty: true,
                })
              }
              disabled={!!selectedOrder}
            >
              <SelectTrigger>
                <SelectValue placeholder="Seleccionar cliente" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="__empty__">Seleccionar</SelectItem>
                {clients.map((client) => (
                  <SelectItem key={client.id} value={String(client.id)}>
                    {client.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            {errors.client_id && (
              <p className="text-sm text-destructive">{errors.client_id.message}</p>
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
                  }
                )
              }
              disabled={!selectedClient || !!selectedOrder}
            >
              <SelectTrigger>
                <SelectValue placeholder="Seleccionar sucursal" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="__empty__">Sin seleccionar</SelectItem>
                {availableBranches.map((branch) => (
                  <SelectItem key={branch.id} value={String(branch.id)}>
                    {branch.name}
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
        </div>

        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          <div className="space-y-1.5">
            <label className="text-sm font-medium">Número</label>
            <Input
              {...register("invoice_number")}
              placeholder="0001-00001234"
            />
            {errors.invoice_number && (
              <p className="text-sm text-destructive">
                {errors.invoice_number.message}
              </p>
            )}
          </div>

          <div className="space-y-1.5">
            <label className="text-sm font-medium">Fecha</label>
            <Input type="date" {...register("invoice_date")} />
            {errors.invoice_date && (
              <p className="text-sm text-destructive">
                {errors.invoice_date.message}
              </p>
            )}
          </div>
        </div>

        <div className="space-y-1.5">
          <label className="text-sm font-medium">Notas</label>
          <Textarea
            {...register("notes")}
            placeholder="Notas internas opcionales"
          />
          {errors.notes && (
            <p className="text-sm text-destructive">{errors.notes.message}</p>
          )}
        </div>
      </section>

      <section className="space-y-4 rounded-2xl border p-4 sm:p-5">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div className="space-y-1">
            <h4 className="text-sm font-semibold">Ítems</h4>
            <p className="text-xs text-muted-foreground">
              Si eliges una orden, los ítems se completan automáticamente.
            </p>
          </div>

          <Button
            type="button"
            variant="outline"
            onClick={() =>
              append({
                product_id: 0,
                product_name: "",
                quantity: 1,
              })
            }
            disabled={!!selectedOrder}
          >
            <Plus className="mr-2 h-4 w-4" />
            Agregar ítem
          </Button>
        </div>

        <div className="space-y-4">
          {fields.map((field, index) => {
            const currentItem = enrichedItems[index];

            return (
              <div
                key={field.id}
                className="grid gap-4 rounded-xl border p-4 sm:grid-cols-2 xl:grid-cols-[1.6fr_140px_auto]"
              >
                <div className="space-y-1.5">
                  <label className="text-sm font-medium">Producto</label>
                  <Select
                    value={
                      Number(currentItem?.product_id) > 0
                        ? String(currentItem.product_id)
                        : "__empty__"
                    }
                    onValueChange={(value) => {
                      const productId =
                        value === "__empty__" ? 0 : Number(value);
                      const selectedProduct = products.find(
                        (p) => p.id === productId
                      );

                      setValue(`items.${index}.product_id`, productId, {
                        shouldValidate: true,
                        shouldDirty: true,
                      });

                      setValue(
                        `items.${index}.product_name`,
                        selectedProduct?.name ?? "",
                        {
                          shouldValidate: true,
                          shouldDirty: true,
                        }
                      );
                    }}
                    disabled={!!selectedOrder}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Seleccionar producto" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="__empty__">Seleccionar</SelectItem>
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

                <div className="space-y-1.5">
                  <label className="text-sm font-medium">Cantidad</label>
                  <Input
                    type="number"
                    min={1}
                    step={1}
                    {...register(`items.${index}.quantity`)}
                    disabled={!!selectedOrder}
                  />
                  {errors.items?.[index]?.quantity && (
                    <p className="text-sm text-destructive">
                      {errors.items[index]?.quantity?.message}
                    </p>
                  )}
                </div>

                <div className="flex items-end sm:col-span-2 xl:col-span-1">
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon"
                    className="w-full sm:w-10"
                    onClick={() => remove(index)}
                    disabled={fields.length === 1 || !!selectedOrder}
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>

                <div className="rounded-lg bg-muted/40 p-3 text-sm text-muted-foreground sm:col-span-2 xl:col-span-3">
                  <span className="font-medium text-foreground">
                    Precio estimado:
                  </span>{" "}
                  {formatCurrency(currentItem?.unitPrice ?? 0)} ·{" "}
                  <span className="font-medium text-foreground">Subtotal:</span>{" "}
                  {formatCurrency(currentItem?.subtotal ?? 0)}
                </div>
              </div>
            );
          })}
        </div>

        <div className="flex justify-start rounded-xl border bg-muted/30 p-4 sm:justify-end">
          <div className="text-left sm:text-right">
            <p className="text-sm text-muted-foreground">Total estimado</p>
            <p className="text-xl font-semibold">
              {formatCurrency(totals.total)}
            </p>
          </div>
        </div>
      </section>

      <div className="flex flex-col gap-3 sm:flex-row sm:justify-end">
        <Button type="submit" disabled={isPending} className="w-full sm:w-auto">
          {isPending ? "Guardando..." : "Crear remito de venta"}
        </Button>
      </div>
    </form>
  );
}