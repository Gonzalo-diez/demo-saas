"use client";

import { useMemo } from "react";
import { useFieldArray, useForm, useWatch } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Plus, Trash2 } from "lucide-react";

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
  editOrderShopSchema,
  type EditOrderShopFormValues,
} from "@/features/admin/orders/schemas/order-schema";
import { useEditOrderShop } from "@/features/admin/orders/hooks/use-edit-order";
import { useProducts } from "@/features/admin/products/hooks/use-products";
import type { AdminOrder } from "@/features/admin/orders/types";

type EditOrderShopFormProps = {
  order: AdminOrder;
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

export function EditOrderShopForm({
  order,
  onSuccess,
}: EditOrderShopFormProps) {
  const editMutation = useEditOrderShop();

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
    watch,
    formState: { errors },
  } = useForm<EditOrderShopFormValues>({
    resolver: zodResolver(editOrderShopSchema),
    defaultValues: {
      customer_name: order.customer_name ?? null,
      customer_phone: order.customer_phone ?? null,
      customer_email: order.customer_email ?? null,
      delivery_type: order.delivery_type ?? null,
      delivery_address: order.delivery_address ?? null,
      delivery_city: order.delivery_city ?? null,
      delivery_reference: order.delivery_reference ?? null,
      preferred_delivery_date: order.preferred_delivery_date ?? null,
      items:
        order.items.length > 0
          ? order.items.map((item) => ({
              product_id: item.product_id,
              quantity: item.quantity,
            }))
          : [{ product_id: 0, quantity: 1 }],
    },
  });

  const { fields, append, remove } = useFieldArray({ control, name: "items" });

  const watchedItems = useWatch({ control, name: "items" });
  const watchedDeliveryType = watch("delivery_type");

  const items = (watchedItems ?? []) as OrderFormItem[];
  const products = productsQuery.data?.items ?? [];

  const enrichedItems = useMemo(() => {
    return items.map((item) => {
      const product = products.find((p) => p.id === Number(item.product_id));
      const unitPrice = Number(product?.unit_price ?? 0);
      const quantity = Number(item.quantity ?? 0);
      return {
        ...item,
        product,
        unitPrice,
        subtotal: unitPrice * quantity,
        stock: product?.stock_current ?? 0,
      };
    });
  }, [items, products]);

  const totalSale = useMemo(
    () => enrichedItems.reduce((acc, i) => acc + i.subtotal, 0),
    [enrichedItems],
  );

  async function onSubmit(data: EditOrderShopFormValues) {
    try {
      await editMutation.mutateAsync({
        orderId: order.id,
        data: {
          customer_name: data.customer_name ?? null,
          customer_phone: data.customer_phone ?? null,
          customer_email: data.customer_email ?? null,
          delivery_type: data.delivery_type ?? null,
          delivery_address: data.delivery_address ?? null,
          delivery_city: data.delivery_city ?? null,
          delivery_reference: data.delivery_reference ?? null,
          preferred_delivery_date: data.preferred_delivery_date ?? null,
          items: data.items.map((item) => ({
            product_id: item.product_id,
            quantity: item.quantity,
          })),
        },
      });
      onSuccess?.();
    } catch (error) {
      console.error("Error editing shop order:", error);
    }
  }

  const isPending = editMutation.isPending || productsQuery.isLoading;
  const isDelivery = watchedDeliveryType === "delivery";

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-5 sm:space-y-6">
      <section className="space-y-4 rounded-2xl border p-4">
        <div className="space-y-1">
          <h4 className="text-sm font-semibold">Datos del cliente</h4>
          <p className="text-xs text-muted-foreground">
            Podés modificar el nombre, teléfono y email del comprador.
          </p>
        </div>

        <div className="grid gap-4 sm:grid-cols-2">
          <div className="space-y-1.5">
            <label className="text-sm font-medium">Nombre</label>
            <Input
              placeholder="Nombre completo"
              {...register("customer_name")}
            />
            {errors.customer_name && (
              <p className="text-sm text-destructive">
                {errors.customer_name.message}
              </p>
            )}
          </div>

          <div className="space-y-1.5">
            <label className="text-sm font-medium">Teléfono</label>
            <Input
              placeholder="Ej: +54 9 11 1234-5678"
              {...register("customer_phone")}
            />
            {errors.customer_phone && (
              <p className="text-sm text-destructive">
                {errors.customer_phone.message}
              </p>
            )}
          </div>

          <div className="space-y-1.5 sm:col-span-2">
            <label className="text-sm font-medium">Email</label>
            <Input
              type="email"
              placeholder="cliente@ejemplo.com"
              {...register("customer_email")}
            />
            {errors.customer_email && (
              <p className="text-sm text-destructive">
                {errors.customer_email.message}
              </p>
            )}
          </div>
        </div>
      </section>

      <section className="space-y-4 rounded-2xl border p-4">
        <div className="space-y-1">
          <h4 className="text-sm font-semibold">Entrega</h4>
          <p className="text-xs text-muted-foreground">
            Tipo de entrega, dirección y fecha preferida.
          </p>
        </div>

        <div className="space-y-1.5">
          <label className="text-sm font-medium">Tipo de entrega</label>
          <Select
            value={watchedDeliveryType ?? "__empty__"}
            onValueChange={(value) =>
              setValue(
                "delivery_type",
                value === "__empty__" ? null : (value as "delivery" | "pickup"),
                { shouldValidate: true, shouldDirty: true },
              )
            }
          >
            <SelectTrigger>
              <SelectValue placeholder="Seleccionar tipo" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="delivery">Envío a domicilio</SelectItem>
              <SelectItem value="pickup">Retiro en local</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {isDelivery && (
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-1.5">
              <label className="text-sm font-medium">Dirección</label>
              <Input
                placeholder="Ej: Av. Corrientes 1234"
                {...register("delivery_address")}
              />
            </div>

            <div className="space-y-1.5">
              <label className="text-sm font-medium">Ciudad</label>
              <Input
                placeholder="Ej: Buenos Aires"
                {...register("delivery_city")}
              />
            </div>

            <div className="space-y-1.5 sm:col-span-2">
              <label className="text-sm font-medium">
                Referencia de entrega
              </label>
              <Input
                placeholder="Ej: Dejar con el encargado del edificio"
                {...register("delivery_reference")}
              />
            </div>
          </div>
        )}

        <div className="space-y-1.5">
          <label className="text-sm font-medium">
            Fecha de entrega preferida
          </label>
          <Input type="date" {...register("preferred_delivery_date")} />
          {errors.preferred_delivery_date && (
            <p className="text-sm text-destructive">
              {errors.preferred_delivery_date.message}
            </p>
          )}
        </div>
      </section>

      <section className="space-y-4 rounded-2xl border p-4">
        <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
          <div className="space-y-1">
            <h4 className="text-sm font-semibold">Productos</h4>
            <p className="text-xs text-muted-foreground">
              Modificá los productos y cantidades del pedido.
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
            const currentStock = currentItem?.stock ?? 0;
            const currentQuantity = Number(items[index]?.quantity ?? 0);
            const exceedsStock =
              currentProduct != null && currentQuantity > currentStock;

            return (
              <div
                key={field.id}
                className="grid gap-3 rounded-2xl border p-4 sm:p-5 md:grid-cols-12"
              >
                <div className="space-y-1.5 md:col-span-5">
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
                        { shouldValidate: true, shouldDirty: true },
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
                      Supera el stock disponible.
                    </p>
                  )}
                </div>

                <div className="space-y-1.5 md:col-span-2">
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

      <section className="rounded-2xl border p-4 sm:p-5">
        <div className="space-y-1">
          <p className="text-xs text-muted-foreground">Total de venta</p>
          <p className="text-lg font-semibold">{formatCurrency(totalSale)}</p>
        </div>
      </section>

      <div className="flex justify-end">
        <Button type="submit" disabled={isPending} className="w-full sm:w-auto">
          {editMutation.isPending ? "Guardando..." : "Guardar cambios"}
        </Button>
      </div>
    </form>
  );
}