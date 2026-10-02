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
  createPurchaseQuoteSchema,
  type CreatePurchaseQuoteFormInput,
  type CreatePurchaseQuoteFormValues,
} from "@/features/admin/purchase-quotes/schemas/purchase-quote-schema";
import { useCreatePurchaseQuote } from "@/features/admin/purchase-quotes/hooks/use-create-purchase-quote";
import { useSuppliers } from "@/features/admin/suppliers/hooks/use-suppliers";
import { useProducts } from "@/features/admin/products/hooks/use-products";

type CreatePurchaseQuoteFormProps = {
  onSuccess?: () => void;
};

function formatCurrency(value: number) {
  return new Intl.NumberFormat("es-AR", {
    style: "currency",
    currency: "ARS",
    maximumFractionDigits: 2,
  }).format(Number.isNaN(value) ? 0 : value);
}

export function CreatePurchaseQuoteForm({ onSuccess }: CreatePurchaseQuoteFormProps) {
  const createPurchaseQuote = useCreatePurchaseQuote();

  const suppliersQuery = useSuppliers({ page: 1, page_size: 20, search: "", status: "active" });

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
  } = useForm<CreatePurchaseQuoteFormInput, undefined, CreatePurchaseQuoteFormValues>({
    resolver: zodResolver(createPurchaseQuoteSchema),
    defaultValues: {
      supplier_id: 0,
      quote_number: "",
      quote_date: "",
      valid_until: "",
      notes: "",
      items: [{ product_id: 0, product_name: "", quantity: 1, unit_cost: 0, discount_amount: 0 }],
    },
  });

  const { fields, append, remove } = useFieldArray({ control, name: "items" });

  const watchedSupplierId = useWatch({ control, name: "supplier_id" });
  const watchedItems = useWatch({ control, name: "items" });

  const supplierId = Number(watchedSupplierId ?? 0);
  const items = watchedItems ?? [];

  const suppliers = suppliersQuery.data?.suppliers ?? [];
  const products = productsQuery.data?.items ?? [];

  const enrichedItems = useMemo(() => {
    return items.map((item) => {
      const quantity = Number(item.quantity ?? 0);
      const unitCost = Number(item.unit_cost ?? 0);
      const discount = Number(item.discount_amount ?? 0);
      const subtotal = quantity * unitCost - discount;

      return { ...item, quantity, unitCost, discount, subtotal };
    });
  }, [items]);

  const totals = useMemo(() => {
    return enrichedItems.reduce(
      (acc, item) => {
        acc.total += item.subtotal;
        return acc;
      },
      { total: 0 }
    );
  }, [enrichedItems]);

  async function onSubmit(data: CreatePurchaseQuoteFormValues) {
    try {
      await createPurchaseQuote.mutateAsync({
        supplier_id: data.supplier_id,
        quote_number: data.quote_number,
        quote_date: data.quote_date,
        valid_until: data.valid_until || null,
        notes: data.notes || null,
        items: data.items.map((item) => ({
          product_id: item.product_id || null,
          product_name: item.product_name,
          quantity: item.quantity,
          unit_cost: item.unit_cost,
          discount_amount: item.discount_amount ?? 0,
        })),
      });

      toast.success("Presupuesto de compra creado correctamente", {
        position: "top-right",
        duration: 4000,
      });

      reset({
        supplier_id: 0,
        quote_number: "",
        quote_date: "",
        valid_until: "",
        notes: "",
        items: [{ product_id: 0, product_name: "", quantity: 1, unit_cost: 0, discount_amount: 0 }],
      });

      onSuccess?.();
    } catch (error) {
      toast.error(
        error instanceof Error ? error.message : "No se pudo crear el presupuesto de compra",
        { position: "top-right", duration: 4000 }
      );
    }
  }

  const isPending =
    createPurchaseQuote.isPending || suppliersQuery.isLoading || productsQuery.isLoading;

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
      <section className="space-y-4 rounded-2xl border p-4 sm:p-5">
        <div className="space-y-1">
          <h4 className="text-sm font-semibold">Datos del presupuesto</h4>
          <p className="text-xs text-muted-foreground">
            Cotización de un proveedor, sin efecto en stock ni cuenta corriente. No se puede
            convertir directamente en remito.
          </p>
        </div>

        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          <div className="space-y-1.5">
            <label className="text-sm font-medium">Proveedor</label>
            <Select
              value={supplierId > 0 ? String(supplierId) : "__empty__"}
              onValueChange={(value) =>
                setValue("supplier_id", value === "__empty__" ? 0 : Number(value), {
                  shouldValidate: true,
                  shouldDirty: true,
                })
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
              <p className="text-sm text-destructive">{errors.supplier_id.message}</p>
            )}
          </div>

          <div className="space-y-1.5">
            <label className="text-sm font-medium">Número</label>
            <Input {...register("quote_number")} placeholder="P-0001" />
            {errors.quote_number && (
              <p className="text-sm text-destructive">{errors.quote_number.message}</p>
            )}
          </div>

          <div className="space-y-1.5">
            <label className="text-sm font-medium">Fecha</label>
            <Input type="date" {...register("quote_date")} />
            {errors.quote_date && (
              <p className="text-sm text-destructive">{errors.quote_date.message}</p>
            )}
          </div>
        </div>

        <div className="grid gap-4 md:grid-cols-2">
          <div className="space-y-1.5">
            <label className="text-sm font-medium">Válido hasta</label>
            <Input type="date" {...register("valid_until")} />
          </div>
        </div>

        <div className="space-y-1.5">
          <label className="text-sm font-medium">Notas</label>
          <Textarea {...register("notes")} placeholder="Notas internas opcionales" />
        </div>
      </section>

      <section className="space-y-4 rounded-2xl border p-4 sm:p-5">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <h4 className="text-sm font-semibold">Ítems</h4>
          <Button
            type="button"
            variant="outline"
            onClick={() =>
              append({ product_id: 0, product_name: "", quantity: 1, unit_cost: 0, discount_amount: 0 })
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
                className="grid gap-4 rounded-xl border p-4 sm:grid-cols-2 xl:grid-cols-[1.4fr_100px_120px_120px_auto]"
              >
                <div className="space-y-1.5">
                  <label className="text-sm font-medium">Producto</label>
                  <Select
                    value={
                      Number(currentItem?.product_id) > 0 ? String(currentItem.product_id) : "__empty__"
                    }
                    onValueChange={(value) => {
                      const productId = value === "__empty__" ? 0 : Number(value);
                      const selectedProduct = products.find((p) => p.id === productId);

                      setValue(`items.${index}.product_id`, productId, {
                        shouldValidate: true,
                        shouldDirty: true,
                      });
                      setValue(`items.${index}.product_name`, selectedProduct?.name ?? "", {
                        shouldValidate: true,
                        shouldDirty: true,
                      });
                      if (selectedProduct?.unit_cost) {
                        setValue(`items.${index}.unit_cost`, Number(selectedProduct.unit_cost), {
                          shouldValidate: true,
                          shouldDirty: true,
                        });
                      }
                    }}
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
                  {errors.items?.[index]?.product_name && (
                    <p className="text-sm text-destructive">
                      {errors.items[index]?.product_name?.message}
                    </p>
                  )}
                </div>

                <div className="space-y-1.5">
                  <label className="text-sm font-medium">Cantidad</label>
                  <Input type="number" min={1} step={1} {...register(`items.${index}.quantity`)} />
                </div>

                <div className="space-y-1.5">
                  <label className="text-sm font-medium">Costo unit.</label>
                  <Input
                    type="number"
                    min={0}
                    step="0.01"
                    {...register(`items.${index}.unit_cost`)}
                  />
                </div>

                <div className="space-y-1.5">
                  <label className="text-sm font-medium">Descuento</label>
                  <Input
                    type="number"
                    min={0}
                    step="0.01"
                    {...register(`items.${index}.discount_amount`)}
                  />
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

                <div className="rounded-lg bg-muted/40 p-3 text-sm text-muted-foreground sm:col-span-2 xl:col-span-5">
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
            <p className="text-xl font-semibold">{formatCurrency(totals.total)}</p>
          </div>
        </div>
      </section>

      <div className="flex flex-col gap-3 sm:flex-row sm:justify-end">
        <Button type="submit" disabled={isPending} className="w-full sm:w-auto">
          {isPending ? "Guardando..." : "Crear presupuesto de compra"}
        </Button>
      </div>
    </form>
  );
}
