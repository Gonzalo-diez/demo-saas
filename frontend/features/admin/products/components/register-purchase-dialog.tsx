"use client";

import { useState } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  PriceMarkupFields,
  type PriceFieldsValue,
} from "@/features/admin/products/components/price-markup-fields";
import { useCreateProductPurchase } from "@/features/admin/products/hooks/use-product-purchases";
import type { Product } from "@/features/admin/products/types";

const money = new Intl.NumberFormat("es-AR", {
  style: "currency",
  currency: "ARS",
  maximumFractionDigits: 2,
});

const today = () => new Date().toISOString().slice(0, 10);

export function RegisterPurchaseDialog({ product }: { product: Product }) {
  const [open, setOpen] = useState(false);
  const createPurchase = useCreateProductPurchase(product.id);

  const [quantity, setQuantity] = useState("");
  const [unitCost, setUnitCost] = useState("");
  // Remarque y precio ligados: lo último que escribiste manda, el otro se calcula.
  const [pricing, setPricing] = useState<PriceFieldsValue>({
    source: null,
    markup: null,
    price: null,
  });
  const [formVersion, setFormVersion] = useState(0);
  const [purchaseDate, setPurchaseDate] = useState(today());
  const [expiryDate, setExpiryDate] = useState("");
  const [notes, setNotes] = useState("");
  const [updatePrice, setUpdatePrice] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const qty = Number(quantity);
  const cost = Number(unitCost);
  const hasPrice = pricing.price != null;

  const reset = () => {
    setQuantity("");
    setUnitCost("");
    setPricing({ source: null, markup: null, price: null });
    setFormVersion((v) => v + 1);
    setExpiryDate("");
    setNotes("");
    setPurchaseDate(today());
    setError(null);
  };

  const submit = async () => {
    setError(null);

    if (!Number.isInteger(qty) || qty <= 0) {
      setError("La cantidad tiene que ser un número entero mayor a 0.");
      return;
    }
    if (unitCost === "" || !Number.isFinite(cost) || cost < 0) {
      setError("Ingresá el costo unitario de esta compra.");
      return;
    }
    if ((pricing.markup != null && pricing.markup < 0) || (pricing.price != null && pricing.price < 0)) {
      setError("El remarque y el precio no pueden ser negativos.");
      return;
    }
    if (expiryDate && expiryDate < purchaseDate) {
      setError("El vencimiento no puede ser anterior a la fecha de compra.");
      return;
    }

    try {
      await createPurchase.mutateAsync({
        quantity: qty,
        unit_cost: cost,
        // Se manda lo que escribió el usuario: con remarque el backend calcula y redondea el
        // precio; con precio se guarda tal cual. Sin ninguno, el precio no se toca.
        ...(pricing.source === "markup" && pricing.markup != null
          ? { markup_percent: pricing.markup }
          : {}),
        ...(pricing.source === "price" && pricing.price != null
          ? { sale_price: pricing.price }
          : {}),
        expiry_date: expiryDate || null,
        purchase_date: purchaseDate || null,
        notes: notes.trim() || null,
        update_product_price: hasPrice ? updatePrice : false,
      });
      toast.success("Compra registrada");
      reset();
      setOpen(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo registrar la compra.");
    }
  };

  return (
    <Dialog
      open={open}
      onOpenChange={(next) => {
        setOpen(next);
        if (!next) setError(null);
      }}
    >
      <DialogTrigger asChild>
        <Button type="button">Registrar compra</Button>
      </DialogTrigger>

      <DialogContent className="max-h-[90vh] overflow-y-auto sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>Registrar compra</DialogTitle>
          <DialogDescription>
            {product.name}. Suma stock, recalcula el costo promedio y queda en el historial.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-1.5">
              <Label htmlFor="purchase-qty">Cantidad</Label>
              <Input
                id="purchase-qty"
                type="number"
                min="1"
                step="1"
                value={quantity}
                onChange={(e) => setQuantity(e.target.value)}
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="purchase-cost">Costo unitario</Label>
              <Input
                id="purchase-cost"
                type="number"
                min="0"
                step="0.01"
                value={unitCost}
                onChange={(e) => setUnitCost(e.target.value)}
              />
            </div>
          </div>

          <div className="space-y-3 rounded-xl border p-3">
            <div>
              <p className="text-sm font-medium">Precio de venta</p>
              <p className="text-xs text-muted-foreground">
                Hoy se vende a {money.format(Number(product.unit_price))}
                {product.markup_percent != null && ` (${Number(product.markup_percent)}% de remarque)`}.
                Dejalo vacío para no tocar el precio.
              </p>
            </div>

            <PriceMarkupFields
              key={`${product.id}-${formVersion}`}
              idPrefix="purchase-pricing"
              unitCost={Number.isFinite(cost) ? cost : 0}
              initialSource={product.markup_percent != null ? "markup" : null}
              initialMarkup={product.markup_percent != null ? Number(product.markup_percent) : null}
              onChange={setPricing}
            />

            {hasPrice && (
              <label className="flex cursor-pointer items-start gap-2 text-sm">
                <input
                  type="checkbox"
                  className="mt-1 h-4 w-4"
                  checked={updatePrice}
                  onChange={(e) => setUpdatePrice(e.target.checked)}
                />
                <span>
                  Usar este precio como precio actual del producto
                  <span className="block text-xs text-muted-foreground">
                    Si lo desmarcás, el precio queda anotado en la compra pero el producto
                    sigue a {money.format(Number(product.unit_price))}.
                  </span>
                </span>
              </label>
            )}
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-1.5">
              <Label htmlFor="purchase-date">Fecha de compra</Label>
              <Input
                id="purchase-date"
                type="date"
                max={today()}
                value={purchaseDate}
                onChange={(e) => setPurchaseDate(e.target.value)}
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="purchase-expiry">Vencimiento (opcional)</Label>
              <Input
                id="purchase-expiry"
                type="date"
                min={purchaseDate || undefined}
                value={expiryDate}
                onChange={(e) => setExpiryDate(e.target.value)}
              />
            </div>
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="purchase-notes">Notas (opcional)</Label>
            <Input
              id="purchase-notes"
              maxLength={500}
              placeholder="Ej: proveedor, lote, factura"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
            />
          </div>

          {error && (
            <p className="rounded-lg bg-destructive/10 px-3 py-2 text-sm font-medium text-destructive">
              {error}
            </p>
          )}

          <div className="flex justify-end gap-2">
            <Button type="button" variant="outline" onClick={() => setOpen(false)}>
              Cancelar
            </Button>
            <Button type="button" onClick={submit} disabled={createPurchase.isPending}>
              {createPurchase.isPending ? "Guardando..." : "Guardar compra"}
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
