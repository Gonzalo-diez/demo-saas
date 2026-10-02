"use client";

import Link from "next/link";
import { useCartStore } from "@/store/cart-store";
import { QuantityStepper } from "@/features/shop/products/components/quantity-stepper";
import { CheckoutForm } from "@/features/shop/cart/components/checkout-form";

export function CheckoutPageClient() {
  const items = useCartStore((s) => s.items);
  const addItem = useCartStore((s) => s.addItem);
  const decreaseItem = useCartStore((s) => s.decreaseItem);
  const deleteItem = useCartStore((s) => s.deleteItem);

  const isEmpty = items.length === 0;
  const total = items.reduce(
    (acc, item) => acc + item.unit_price * item.quantity,
    0,
  );

  return (
    <main className="mx-auto max-w-5xl px-4 py-8 sm:px-6">
      <div className="mb-8 flex items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold sm:text-3xl">Checkout</h1>
          <p className="text-sm text-muted-foreground">
            Revisá tu pedido antes de enviarlo.
          </p>
        </div>

        <Link
          href="/"
          className="rounded-md border px-4 py-2 text-sm font-medium hover:bg-muted"
        >
          Seguir comprando
        </Link>
      </div>

      {isEmpty ? (
        <section className="rounded-xl border bg-card p-8 text-center shadow-sm">
          <h2 className="text-xl font-semibold">Tu carrito está vacío</h2>
          <p className="mt-2 text-sm text-muted-foreground">
            Agregá productos desde el catálogo para continuar.
          </p>

          <Link
            href="/"
            className="mt-6 inline-flex rounded-md bg-primary px-5 py-3 text-sm font-medium text-primary-foreground"
          >
            Ir al catálogo
          </Link>
        </section>
      ) : (
        <div className="grid gap-6 lg:grid-cols-[1.4fr_0.9fr]">
          <section className="rounded-xl border bg-card p-4 shadow-sm sm:p-6 max-h-[68vh] overflow-y-auto">
            <h2 className="mb-4 text-lg font-semibold sm:text-xl">Productos</h2>

            <div className="space-y-4">
              {items.map((item) => (
                <article
                  key={item.id}
                  className="flex flex-col gap-4 rounded-lg border p-4 sm:flex-row sm:items-center sm:justify-between"
                >
                  <div className="min-w-0">
                    {item.category && (
                      <p className="text-xs uppercase tracking-wide text-muted-foreground">
                        {item.category}
                      </p>
                    )}

                    <h3 className="truncate text-sm font-medium sm:text-base">
                      {item.name}
                    </h3>

                    <p className="mt-1 text-base font-bold">
                      ${item.unit_price.toLocaleString("es-AR")}
                    </p>
                  </div>

                  <div className="flex flex-col gap-3 sm:items-end">
                    <div className="w-full sm:w-[140px]">
                      <QuantityStepper
                        quantity={item.quantity}
                        onDecrease={() => decreaseItem(item.id)}
                        onIncrease={() => addItem(item)}
                      />
                    </div>

                    <button
                      type="button"
                      onClick={() => deleteItem(item.id)}
                      className="text-sm font-medium text-stamp hover:underline"
                    >
                      Eliminar
                    </button>
                  </div>
                </article>
              ))}
            </div>
          </section>

          <aside className="h-fit rounded-xl border bg-card p-4 shadow-sm sm:p-6">
            <h2 className="mb-4 text-lg font-semibold sm:text-xl">Resumen</h2>

            <div className="mb-6 flex items-center justify-between text-sm">
              <span>Total</span>
              <span className="text-lg font-bold">
                ${total.toLocaleString("es-AR")}
              </span>
            </div>

            <CheckoutForm />
          </aside>
        </div>
      )}
    </main>
  );
}