"use client";

import { useEffect, useMemo, useState } from "react";
import { toast } from "sonner";
import { Search, Trash2, Plus } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { QuantityStepper } from "@/features/shop/products/components/quantity-stepper";
import { getAllProducts } from "@/features/shop/products/apis/product-shop-api";
import {
  useOrderPublic,
  useEditOrderPublic,
} from "@/features/shop/orders/hooks/use-order-public";
import { EDITABLE_ORDER_STATUSES } from "@/features/shop/orders/types";
import type { ShopProduct } from "@/features/shop/products/types";

type EditableItem = {
  product_id: number;
  name: string;
  brand: string | null;
  sku: string | null;
  image_url: string | null;
  unit_price: number;
  quantity: number;
};

const ORDER_STATUS_LABELS: Record<string, string> = {
  pending_confirmation: "Pendiente de confirmación",
  confirmed: "Confirmado",
  preparing: "En preparación",
  shipped: "Enviado",
  delivered: "Entregado",
  cancelled: "Cancelado",
};

type Props = {
  orderId: number;
  token: string;
};

export function EditOrderClient({ orderId, token }: Props) {
  const { data: order, isLoading, isError } = useOrderPublic(orderId, token);
  const editMutation = useEditOrderPublic(orderId, token);

  const [items, setItems] = useState<EditableItem[]>([]);

  const [search, setSearch] = useState("");
  const [showPicker, setShowPicker] = useState(false);
  const [catalog, setCatalog] = useState<ShopProduct[]>([]);
  const [catalogLoading, setCatalogLoading] = useState(false);

  // Precargamos los items actuales del pedido una sola vez, cuando llega la
  // data (order pasa de undefined a definido). Ajustamos el estado durante
  // el render en vez de en un efecto para evitar un render en cascada:
  // https://react.dev/learn/you-might-not-need-an-effect
  const [initializedOrderId, setInitializedOrderId] = useState<number | null>(null);
  if (order && order.id !== initializedOrderId) {
    setInitializedOrderId(order.id);
    setItems(
      order.items.map((item) => ({
        product_id: item.product_id,
        name: item.product_name_snapshot,
        brand: item.product_brand_snapshot,
        sku: item.product_sku_snapshot,
        image_url: item.product_image_url_snapshot,
        unit_price: item.unit_price,
        quantity: item.quantity,
      })),
    );
  }

  // Fetch de productos para el picker. `catalogLoading` se pone en `true`
  // dentro del efecto porque depende de la respuesta async que dispara el
  // propio efecto (patrón estándar de data-fetching); no se puede resolver
  // ajustando estado durante el render sin duplicar esta misma lógica.
  useEffect(() => {
    if (!showPicker) return;

    let cancelled = false;
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setCatalogLoading(true);

    getAllProducts({ is_active: true, search: search || undefined })
      .then((products) => {
        if (!cancelled) setCatalog(products);
      })
      .finally(() => {
        if (!cancelled) setCatalogLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [showPicker, search]);

  const total = useMemo(
    () => items.reduce((acc, item) => acc + item.unit_price * item.quantity, 0),
    [items],
  );

  const canEdit = order ? EDITABLE_ORDER_STATUSES.has(order.status) : false;

  const handleIncrease = (productId: number) => {
    setItems((prev) =>
      prev.map((item) =>
        item.product_id === productId
          ? { ...item, quantity: item.quantity + 1 }
          : item,
      ),
    );
  };

  const handleDecrease = (productId: number) => {
    setItems((prev) =>
      prev
        .map((item) =>
          item.product_id === productId
            ? { ...item, quantity: item.quantity - 1 }
            : item,
        )
        .filter((item) => item.quantity > 0),
    );
  };

  const handleRemove = (productId: number) => {
    setItems((prev) => prev.filter((item) => item.product_id !== productId));
  };

  const handleAddProduct = (product: ShopProduct) => {
    setItems((prev) => {
      const existing = prev.find((item) => item.product_id === product.id);

      if (existing) {
        return prev.map((item) =>
          item.product_id === product.id
            ? { ...item, quantity: item.quantity + 1 }
            : item,
        );
      }

      return [
        ...prev,
        {
          product_id: product.id,
          name: product.name,
          brand: product.brand,
          sku: product.sku,
          image_url: product.image_url,
          unit_price: product.unit_price,
          quantity: 1,
        },
      ];
    });
  };

  const handleSave = async () => {
    if (items.length === 0) {
      toast.error("Tu pedido no puede quedar sin productos.");
      return;
    }

    try {
      await editMutation.mutateAsync({
        items: items.map((item) => ({
          product_id: item.product_id,
          quantity: item.quantity,
        })),
      });
      toast.success("¡Listo! Actualizamos tu pedido y te avisamos por WhatsApp.");
    } catch (error) {
      toast.error(
        error instanceof Error
          ? error.message
          : "No pudimos guardar los cambios. Probá de nuevo.",
      );
    }
  };

  if (isLoading) {
    return (
      <main className="mx-auto max-w-3xl px-4 py-12 text-center">
        <p className="text-sm text-muted-foreground">Cargando tu pedido...</p>
      </main>
    );
  }

  if (isError || !order) {
    return (
      <main className="mx-auto max-w-3xl px-4 py-12 text-center">
        <h1 className="text-xl font-semibold">No pudimos abrir tu pedido</h1>
        <p className="mt-2 text-sm text-muted-foreground">
          El link puede haber vencido o ser inválido. Pedí uno nuevo escribiéndonos
          por WhatsApp.
        </p>
      </main>
    );
  }

  if (!canEdit) {
    return (
      <main className="mx-auto max-w-3xl px-4 py-12 text-center">
        <h1 className="text-xl font-semibold">Este pedido ya no se puede editar</h1>
        <p className="mt-2 text-sm text-muted-foreground">
          Tu pedido #{order.id} está en estado &quot;
          {ORDER_STATUS_LABELS[order.status] ?? order.status}&quot;. Si necesitás
          hacer un cambio, contactanos directamente por WhatsApp.
        </p>
      </main>
    );
  }

  return (
    <main className="mx-auto max-w-3xl px-4 py-8 sm:px-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold sm:text-3xl">Editar pedido #{order.id}</h1>
        <p className="text-sm text-muted-foreground">
          Agregá o quitá productos. Al confirmar, te avisamos por WhatsApp.
        </p>
      </div>

      <section className="rounded-xl border bg-card p-4 shadow-sm sm:p-6">
        <h2 className="mb-4 text-lg font-semibold">Productos</h2>

        {items.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            No quedan productos en el pedido. Agregá alguno para poder guardar.
          </p>
        ) : (
          <div className="space-y-4">
            {items.map((item) => (
              <article
                key={item.product_id}
                className="flex items-center gap-3 border-b pb-4 last:border-b-0 last:pb-0"
              >
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm font-medium">{item.name}</p>
                  {item.brand && (
                    <p className="text-xs text-muted-foreground">{item.brand}</p>
                  )}
                  <p className="text-xs text-muted-foreground">
                    ${item.unit_price.toLocaleString("es-AR")} c/u
                  </p>
                </div>

                <div className="w-32 shrink-0">
                  <QuantityStepper
                    quantity={item.quantity}
                    onIncrease={() => handleIncrease(item.product_id)}
                    onDecrease={() => handleDecrease(item.product_id)}
                  />
                </div>

                <button
                  type="button"
                  onClick={() => handleRemove(item.product_id)}
                  className="shrink-0 rounded-md p-2 text-muted-foreground hover:bg-destructive/10 hover:text-destructive"
                  aria-label={`Quitar ${item.name}`}
                >
                  <Trash2 className="size-4" />
                </button>
              </article>
            ))}
          </div>
        )}

        <Button
          variant="outline"
          className="mt-4 w-full"
          onClick={() => setShowPicker((v) => !v)}
        >
          <Plus className="size-4" />
          Agregar productos
        </Button>

        {showPicker && (
          <div className="mt-4 rounded-lg border p-3">
            <div className="relative mb-3">
              <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                placeholder="Buscar producto..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="pl-9"
              />
            </div>

            <div className="max-h-64 space-y-2 overflow-y-auto">
              {catalogLoading ? (
                <p className="py-4 text-center text-sm text-muted-foreground">
                  Buscando...
                </p>
              ) : catalog.length === 0 ? (
                <p className="py-4 text-center text-sm text-muted-foreground">
                  No encontramos productos.
                </p>
              ) : (
                catalog.map((product) => (
                  <button
                    key={product.id}
                    type="button"
                    onClick={() => handleAddProduct(product)}
                    disabled={product.stock_current <= 0}
                    className="flex w-full items-center justify-between rounded-md border px-3 py-2 text-left text-sm hover:bg-muted disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    <span className="truncate">{product.name}</span>
                    <span className="shrink-0 text-muted-foreground">
                      ${product.unit_price.toLocaleString("es-AR")}
                    </span>
                  </button>
                ))
              )}
            </div>
          </div>
        )}
      </section>

      <section className="mt-6 rounded-xl border bg-card p-4 shadow-sm sm:p-6">
        <div className="flex items-center justify-between text-lg font-semibold">
          <span>Total estimado</span>
          <span>
            {order.currency} {total.toLocaleString("es-AR")}
          </span>
        </div>
        <p className="mt-1 text-xs text-muted-foreground">
          El total final se confirma al guardar, por si algún precio cambió.
        </p>

        <Button
          className="mt-4 w-full"
          size="lg"
          disabled={editMutation.isPending || items.length === 0}
          onClick={handleSave}
        >
          {editMutation.isPending ? "Guardando..." : "Guardar cambios"}
        </Button>
      </section>
    </main>
  );
}