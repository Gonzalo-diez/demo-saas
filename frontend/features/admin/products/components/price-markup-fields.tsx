"use client";

import { useEffect, useRef, useState } from "react";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { priceFromMarkup } from "@/lib/pricing";

export type PriceSource = "markup" | "price";

export type PriceFieldsValue = {
  /** Cuál de los dos campos escribió el usuario por última vez (el otro se calcula). */
  source: PriceSource | null;
  markup: number | null;
  price: number | null;
};

type Props = {
  unitCost: number;
  initialSource?: PriceSource | null;
  initialMarkup?: number | null;
  initialPrice?: number | null;
  onChange: (value: PriceFieldsValue) => void;
  idPrefix?: string;
};

const money = new Intl.NumberFormat("es-AR", {
  style: "currency",
  currency: "ARS",
  maximumFractionDigits: 2,
});

const round2 = (n: number) => Math.round(n * 100) / 100;
const isNum = (text: string) => text.trim() !== "" && Number.isFinite(Number(text));

/** Dado el campo que manda, calcula el otro. */
export function deriveLinkedPrice(source: PriceSource | null, markupText: string, priceText: string, cost: number) {
  if (source === "markup") {
    if (!isNum(markupText)) return { markupText, priceText: "" };
    // Con remarque el precio se redondea al peso entero (400,50 -> 401).
    return { markupText, priceText: String(priceFromMarkup(cost, Number(markupText))) };
  }
  if (source === "price") {
    if (!isNum(priceText)) return { markupText: "", priceText };
    if (!(cost > 0)) return { markupText: "", priceText };
    return { markupText: String(round2((Number(priceText) / cost - 1) * 100)), priceText };
  }
  return { markupText, priceText };
}

/**
 * Remarque (%) y precio de venta ligados: si escribís el remarque se calcula el precio
 * (redondeado al peso entero) y si ajustás el precio se calcula el remarque que resulta
 * sobre el costo. Si cambia el costo, se recalcula el que NO escribiste.
 */
export function PriceMarkupFields({
  unitCost,
  initialSource = null,
  initialMarkup = null,
  initialPrice = null,
  onChange,
  idPrefix = "pricing",
}: Props) {
  const [source, setSource] = useState<PriceSource | null>(initialSource);
  const [markupText, setMarkupText] = useState(
    initialMarkup != null ? String(round2(initialMarkup)) : "",
  );
  const [priceText, setPriceText] = useState(
    initialPrice != null ? String(initialPrice) : "",
  );

  const onChangeRef = useRef(onChange);
  useEffect(() => {
    onChangeRef.current = onChange;
  });

  const emit = (src: PriceSource | null, m: string, p: string) =>
    onChangeRef.current({
      source: src,
      markup: isNum(m) ? Number(m) : null,
      price: isNum(p) ? Number(p) : null,
    });

  // Cambió el costo: se recalcula el campo que no escribió el usuario.
  const firstRun = useRef(true);
  useEffect(() => {
    if (firstRun.current) {
      firstRun.current = false;
      // Al abrir: si ya hay precio, se muestra el % que resulta sobre el costo.
      if (initialSource === "price" && initialPrice != null) {
        const next = deriveLinkedPrice("price", markupText, String(initialPrice), unitCost);
        setMarkupText(next.markupText);
      }
      return;
    }
    if (!source) return;
    const next = deriveLinkedPrice(source, markupText, priceText, unitCost);
    setMarkupText(next.markupText);
    setPriceText(next.priceText);
    emit(source, next.markupText, next.priceText);
    // Solo reaccionamos al costo: markupText/priceText los maneja el usuario.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [unitCost]);

  const handleMarkup = (value: string) => {
    const next = deriveLinkedPrice("markup", value, priceText, unitCost);
    setSource("markup");
    setMarkupText(value);
    setPriceText(next.priceText);
    emit("markup", value, next.priceText);
  };

  const handlePrice = (value: string) => {
    const next = deriveLinkedPrice("price", markupText, value, unitCost);
    setSource("price");
    setPriceText(value);
    setMarkupText(next.markupText);
    emit("price", next.markupText, value);
  };

  const price = isNum(priceText) ? Number(priceText) : null;
  const markup = isNum(markupText) ? Number(markupText) : null;
  const belowCost = price != null && unitCost > 0 && price < unitCost;

  return (
    <div className="space-y-3">
      <div className="grid gap-4 sm:grid-cols-2">
        <div className="space-y-1.5">
          <Label htmlFor={`${idPrefix}-markup`}>Remarque sobre el costo (%)</Label>
          <Input
            id={`${idPrefix}-markup`}
            type="number"
            step="0.01"
            min="0"
            inputMode="decimal"
            placeholder="Ej: 40"
            value={markupText}
            onChange={(e) => handleMarkup(e.target.value)}
          />
        </div>

        <div className="space-y-1.5">
          <Label htmlFor={`${idPrefix}-price`}>Precio de venta</Label>
          <Input
            id={`${idPrefix}-price`}
            type="number"
            step="0.01"
            min="0"
            inputMode="decimal"
            placeholder="Ej: 280"
            value={priceText}
            onChange={(e) => handlePrice(e.target.value)}
          />
        </div>
      </div>

      <p className="text-xs text-muted-foreground">
        {!(unitCost > 0)
          ? "Cargá el costo para calcular el remarque y el precio."
          : source === "price"
            ? `Con este precio ganás ${money.format((price ?? 0) - unitCost)} por unidad: ${
                markup != null ? `${markup}%` : "—"
              } sobre el costo.`
            : "Escribí el remarque y el precio se calcula (redondeado al peso entero, 400,50 → 401), o ajustá el precio y te muestro el %."}
      </p>

      {belowCost && (
        <p className="rounded-lg bg-amber-100 px-3 py-2 text-xs font-medium text-amber-900 dark:bg-amber-950 dark:text-amber-200">
          Este precio está por debajo del costo: vendés con pérdida.
        </p>
      )}
    </div>
  );
}
