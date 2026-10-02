"use client";

import { useMemo } from "react";
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
  createPurchaseInvoiceSchema,
  type CreatePurchaseInvoiceFormInput,
  type CreatePurchaseInvoiceFormValues,
} from "@/features/admin/purchase-invoices/schemas/purchase-invoice-schema";
import { useCreatePurchaseInvoice } from "@/features/admin/purchase-invoices/hooks/use-create-purchase-invoice";
import { useSuppliers } from "@/features/admin/suppliers/hooks/use-suppliers";
import { useProducts } from "@/features/admin/products/hooks/use-products";

type CreatePurchaseInvoiceFormProps = {
  onSuccess?: () => void;
};

type PurchaseFormItem = {
  product_id: number;
  quantity: number;
  unit_cost: number;
};

function formatCurrency(value: number) {
  return new Intl.NumberFormat("es-AR", {
    style: "currency",
    currency: "ARS",
    maximumFractionDigits: 2,
  }).format(Number.isNaN(value) ? 0 : value);
}

export function CreatePurchaseInvoiceForm({
  onSuccess,
}: CreatePurchaseInvoiceFormProps) {
  const createPurchaseInvoice = useCreatePurchaseInvoice();

  const suppliersQuery = useSuppliers({
    page: 1,
    page_size: 20,
    search: "",
    status: "active",
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
  } = useForm<
    CreatePurchaseInvoiceFormInput,
    undefined,
    CreatePurchaseInvoiceFormValues
  >({
    resolver: zodResolver(createPurchaseInvoiceSchema),
    defaultValues: {
      supplier_id: 0,
      invoice_number: "",
      invoice_date: "",
      notes: "",
      items: [{ product_id: 0, quantity: 1, unit_cost: 0 }],
    },
  });

  const { fields, append, remove } = useFieldArray({
    control,
    name: "items",
  });

  const watchedSupplierId = useWatch({
    control,
    name: "supplier_id",
  });

  const watchedItems = useWatch({
    control,
    name: "items",
  });

  const supplierId = Number(watchedSupplierId ?? 0);
  const items = (watchedItems ?? []) as PurchaseFormItem[];

  const suppliers = suppliersQuery.data?.suppliers ?? [];
  const products = productsQuery.data?.items ?? [];

  const selectedSupplier =
    suppliers.find((supplier) => supplier.id === supplierId) ?? null;

  const enrichedItems = useMemo(() => {
    return items.map((item) => {
      const product = products.find((p) => p.id === Number(item.product_id));
      const quantity = Number(item.quantity ?? 0);
      const unitCost = Number(item.unit_cost ?? 0);
      const subtotal = quantity * unitCost;

      return {
        ...item,
        product,
        unitCost,
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

  async function onSubmit(data: CreatePurchaseInvoiceFormValues) {
    try {
      if (!selectedSupplier) {
        toast.error("Seleccioná un proveedor válido", {
          position: "top-right",
          duration: 4000,
        });
        return;
      }

      const payload = {
        supplier_id: selectedSupplier.id,
        supplier_name: selectedSupplier.name,
        supplier_tax_id: selectedSupplier.tax_id ?? null,
        invoice_number: data.invoice_number,
        invoice_date: data.invoice_date,
        notes: data.notes || null,
        items: data.items.map((item) => {
          const product = products.find((p) => p.id === item.product_id);

          return {
            product_id: item.product_id,
            product_name: product?.name ?? "",
            product_sku: product?.sku ?? null,
            quantity: item.quantity,
            unit_cost: item.unit_cost,
          };
        }),
      };

      await createPurchaseInvoice.mutateAsync(payload);

      toast.success("Remito de compra creada correctamente", {
        position: "top-right",
        duration: 4000,
      });

      reset({
        supplier_id: 0,
        invoice_number: "",
        invoice_date: "",
        notes: "",
        items: [{ product_id: 0, quantity: 1, unit_cost: 0 }],
      });

      onSuccess?.();
    } catch (error) {
      toast.error(
        error instanceof Error
          ? error.message
          : "No se pudo crear el remito de compra",
        {
          position: "top-right",
          duration: 4000,
        }
      );
    }
  }

  const isPending =
    createPurchaseInvoice.isPending ||
    suppliersQuery.isLoading ||
    productsQuery.isLoading;

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
      <section className="space-y-4 rounded-2xl border p-4 sm:p-5">
        <div className="space-y-1">
          <h4 className="text-sm font-semibold">Datos del remito</h4>
          <p className="text-xs text-muted-foreground">
            Seleccioná el proveedor y completá los datos básicos del remito.
          </p>
        </div>

        <div className="grid gap-4 md:grid-cols-2">
          <div className="space-y-1.5">
            <label className="text-sm font-medium">Proveedor</label>
            <Select
              value={supplierId > 0 ? String(supplierId) : "__empty__"}
              onValueChange={(value) =>
                setValue(
                  "supplier_id",
                  value === "__empty__" ? 0 : Number(value),
                  {
                    shouldValidate: true,
                    shouldDirty: true,
                  }
                )
              }
            >
              <SelectTrigger>
                <SelectValue placeholder="Seleccionar proveedor" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="__empty__">Seleccionar</SelectItem>
                {suppliers.map((supplier) => (
                  <SelectItem key={supplier.id} value={String(supplier.id)}>
                    {supplier.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            {errors.supplier_id && (
              <p className="text-sm text-destructive">
                {errors.supplier_id.message}
              </p>
            )}
          </div>
        </div>

        <div className="grid gap-4 md:grid-cols-2">
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
              Agregá los productos comprados y su costo unitario.
            </p>
          </div>

          <Button
            type="button"
            variant="outline"
            onClick={() =>
              append({
                product_id: 0,
                quantity: 1,
                unit_cost: 0,
              })
            }
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
                className="grid gap-4 rounded-xl border p-4 sm:grid-cols-2 xl:grid-cols-[1.4fr_140px_160px_auto]"
              >
                <div className="space-y-1.5">
                  <label className="text-sm font-medium">Producto</label>
                  <Select
                    value={
                      Number(currentItem?.product_id) > 0
                        ? String(currentItem.product_id)
                        : "__empty__"
                    }
                    onValueChange={(value) =>
                      setValue(
                        `items.${index}.product_id`,
                        value === "__empty__" ? 0 : Number(value),
                        {
                          shouldValidate: true,
                          shouldDirty: true,
                        }
                      )
                    }
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
                  />
                  {errors.items?.[index]?.quantity && (
                    <p className="text-sm text-destructive">
                      {errors.items[index]?.quantity?.message}
                    </p>
                  )}
                </div>

                <div className="space-y-1.5">
                  <label className="text-sm font-medium">Costo unitario</label>
                  <Input
                    type="number"
                    min={0}
                    step="0.01"
                    {...register(`items.${index}.unit_cost`)}
                  />
                  {errors.items?.[index]?.unit_cost && (
                    <p className="text-sm text-destructive">
                      {errors.items[index]?.unit_cost?.message}
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
                    disabled={fields.length === 1}
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>

                <div className="rounded-lg bg-muted/40 p-3 text-sm text-muted-foreground sm:col-span-2 xl:col-span-4">
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
          {isPending ? "Guardando..." : "Crear remito de compra"}
        </Button>
      </div>
    </form>
  );
}