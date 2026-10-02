"use client";

import { useEffect, useMemo } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { CalendarDays, Store } from "lucide-react";
import { useCartStore } from "@/store/cart-store";
import { useClientAuthStore } from "@/features/shop/auth/store/auth-store";
import { toast } from "sonner";

import { Label } from "@/components/ui/label";
import {
  createOrderShopSchema,
  type CreateOrderShopFormValues,
} from "@/features/shop/cart/schemas/order-shop-schema";
import { useCreateOrderShop } from "@/features/shop/cart/hooks/use-create-order-shop";
import { useCheckoutStorage } from "@/features/shop/cart/hooks/use-checkout-storage";
import { useClientBranches } from "@/features/shop/cart/hooks/use-client-branches";

function toInputDate(d: Date) {
  return d.toISOString().split("T")[0];
}

function getTodayString() {
  return toInputDate(new Date());
}

function getMaxDateString() {
  const d = new Date();
  d.setDate(d.getDate() + 30);
  return toInputDate(d);
}

export function CheckoutForm() {
  const items = useCartStore((s) => s.items);
  const clearCart = useCartStore((s) => s.clearCart);
  const client = useClientAuthStore((s) => s.client);

  const { mutate: createOrder, isPending } = useCreateOrderShop();
  const { savedData, saveData, clearData } = useCheckoutStorage();
  const { data: branches } = useClientBranches();

  const total = items.reduce(
    (acc, item) => acc + item.unit_price * item.quantity,
    0,
  );
  const totalLabel = useMemo(() => total.toLocaleString("es-AR"), [total]);

  const {
    register,
    handleSubmit,
    watch,
    reset,
    setValue,
    getValues,
    formState: { errors },
  } = useForm<CreateOrderShopFormValues>({
    resolver: zodResolver(createOrderShopSchema(false)),
    defaultValues: {
      delivery_type: "delivery",
    },
  });

  // Populate form with stored data once it's loaded from localStorage
  useEffect(() => {
    if (savedData && Object.keys(savedData).length > 0) {
      reset((current) => ({ ...current, ...savedData }), {
        keepDefaultValues: false,
      });
    } else if (savedData && client) {
      // Sin nada guardado todavía: completamos con los datos de la
      // cuenta del cliente logueado, para no pedirle de nuevo algo
      // que ya sabemos.
      reset(
        (current) => ({
          ...current,
          customer_name: client.name ?? current.customer_name,
          customer_phone: client.phone ?? current.customer_phone,
          customer_email: client.email ?? current.customer_email,
          customer_tax_id: client.tax_id ?? current.customer_tax_id,
        }),
        { keepDefaultValues: false },
      );
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [savedData, client, reset]);

  // Una vez que cargan las sucursales del cliente, preseleccionamos la
  // principal (si no había ninguna ya elegida/guardada). Si el cliente
  // no tiene sucursales cargadas, esto no hace nada.
  useEffect(() => {
    if (!branches || branches.length === 0) return;
    if (getValues("client_branch_id")) return;

    const main = branches.find((b) => b.is_main) ?? branches[0];
    setValue("client_branch_id", main.id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [branches]);

  const deliveryType = watch("delivery_type");
  const isDelivery = deliveryType === "delivery";

  const todayStr = getTodayString();
  const maxDateStr = getMaxDateString();

  // Save to localStorage whenever relevant fields change
  const watchedFields = watch([
    "customer_name",
    "customer_phone",
    "customer_email",
    "customer_person_type",
    "customer_iva_condition",
    "delivery_type",
    "delivery_address",
    "delivery_city",
    "delivery_reference",
    "client_branch_id",
    "document_type",
  ]);

  useEffect(() => {
    const [
      customer_name,
      customer_phone,
      customer_email,
      customer_person_type,
      customer_iva_condition,
      delivery_type,
      delivery_address,
      delivery_city,
      delivery_reference,
      client_branch_id,
      document_type,
    ] = watchedFields;

    // Only save once the user has started filling in data
    if (!customer_name && !customer_phone && !customer_email) return;

    saveData({
      customer_name,
      customer_phone,
      customer_email,
      customer_person_type,
      customer_iva_condition,
      delivery_type: delivery_type as "delivery" | "pickup",
      delivery_address,
      delivery_city,
      delivery_reference,
      client_branch_id,
      document_type,
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [watchedFields]);

  async function onSubmit(data: CreateOrderShopFormValues) {
    if (items.length === 0) {
      toast.error("Tu carrito está vacío");
      return;
    }

    const payload = {
      ...data,
      items: items.map((item) => ({
        product_id: item.id,
        quantity: item.quantity,
      })),
    };

    createOrder(payload, {
      onSuccess: () => {
        const totalItems = items.reduce((acc, item) => acc + item.quantity, 0);

        toast.success("¡Pedido enviado!", {
          description: `Orden por $${total.toLocaleString("es-AR")}, ${totalItems} artículos.`,
          duration: 5000,
        });

        clearCart();
        // Keep personal data saved — only clear the date field
        reset({
          customer_name: data.customer_name,
          customer_phone: data.customer_phone,
          customer_email: data.customer_email,

          customer_tax_id: data.customer_tax_id,
          customer_person_type: data.customer_person_type,
          customer_iva_condition: data.customer_iva_condition,

          customer_dni: "",
          age_confirmed: false,

          delivery_type: data.delivery_type,
          delivery_address: data.delivery_address,
          delivery_city: data.delivery_city,
          delivery_reference: data.delivery_reference,

          client_branch_id: data.client_branch_id,

          document_type: data.document_type,

          preferred_delivery_date: "",
        });
      },
      onError: (error) => {
        toast.error("Error al crear el pedido", {
          description: error.message,
        });
      },
    });
  }

  // While localStorage hasn't loaded yet, show skeleton to avoid flicker
  if (savedData === null) {
    return (
      <div className="space-y-4 animate-pulse">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="h-12 w-full rounded-md bg-muted" />
        ))}
      </div>
    );
  }

  const hasSavedData =
    savedData.customer_name ||
    savedData.customer_phone ||
    savedData.customer_email;

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      {/* Notice when data was prefilled */}
      {hasSavedData && (
        <div className="flex items-center justify-between rounded-md bg-muted border px-3 py-2 text-xs text-muted-foreground">
          <span>Tus datos fueron completados automáticamente.</span>
          <button
            type="button"
            onClick={() => {
              clearData();
              reset({
                delivery_type: "delivery",
                customer_name: "",
                customer_phone: "",
                customer_email: "",
                customer_tax_id: "",
                customer_person_type: undefined,
                customer_iva_condition: undefined,
                customer_dni: "",
                delivery_address: "",
                delivery_city: "",
                delivery_reference: "",
                preferred_delivery_date: "",
                age_confirmed: false,
                document_type: undefined,
              });
            }}
            className="ml-3 text-xs underline hover:text-foreground transition-colors"
          >
            Limpiar
          </button>
        </div>
      )}

      <div className="space-y-1.5">
        <Label htmlFor="customer_name">Nombre completo</Label>
        <input
          id="customer_name"
          {...register("customer_name")}
          placeholder="Ej: Juan García"
          className="w-full rounded-md border border-input bg-background px-3 py-2.5 text-sm outline-none transition-colors focus:ring-2 focus:ring-ring/50"
        />
        {errors.customer_name && (
          <p className="text-xs text-destructive font-medium">
            {errors.customer_name.message}
          </p>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="space-y-1.5">
          <Label htmlFor="customer_phone">WhatsApp</Label>
          <input
            id="customer_phone"
            {...register("customer_phone")}
            placeholder="Ej: 1122334455"
            className="w-full rounded-md border border-input bg-background px-3 py-2.5 text-sm outline-none transition-colors focus:ring-2 focus:ring-ring/50"
          />
          {errors.customer_phone && (
            <p className="text-xs text-destructive font-medium">
              {errors.customer_phone.message}
            </p>
          )}
        </div>

        <div className="space-y-1.5">
          <Label htmlFor="customer_email">Email</Label>
          <input
            id="customer_email"
            {...register("customer_email")}
            placeholder="para recibir el detalle"
            className="w-full rounded-md border border-input bg-background px-3 py-2.5 text-sm outline-none transition-colors focus:ring-2 focus:ring-ring/50"
          />
          {errors.customer_email && (
            <p className="text-xs text-destructive font-medium">
              {errors.customer_email.message}
            </p>
          )}
        </div>
      </div>

      {branches && branches.length > 0 && (
        <div className="space-y-1.5 rounded-lg border bg-muted/40 p-4">
          <Label htmlFor="client_branch_id" className="flex items-center gap-2">
            <Store className="h-4 w-4 text-muted-foreground" />
            Sucursal
          </Label>
          <p className="text-xs text-muted-foreground">
            ¿A cuál de tus sucursales corresponde este pedido?
          </p>

          <select
            id="client_branch_id"
            disabled={branches.length === 1}
            {...register("client_branch_id", { valueAsNumber: true })}
            className="w-full rounded-md border border-input bg-background px-3 py-2.5 text-sm outline-none transition-colors focus:ring-2 focus:ring-ring/50 disabled:opacity-70"
          >
            {branches.map((branch) => (
              <option key={branch.id} value={branch.id}>
                {branch.name}
                {branch.is_main ? " (Principal)" : ""}
              </option>
            ))}
          </select>

          {errors.client_branch_id && (
            <p className="text-xs text-destructive font-medium">
              {errors.client_branch_id.message}
            </p>
          )}
        </div>
      )}

      <div className="space-y-4 rounded-lg border bg-muted/40 p-4">
        <div>
          <h3 className="text-sm font-semibold">Datos de facturación</h3>
          <p className="mt-1 text-xs text-muted-foreground">
            Completá estos datos si necesitás un remito con tus datos fiscales.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="space-y-1.5">
            <Label htmlFor="customer_person_type">Tipo de persona</Label>

            <select
              id="customer_person_type"
              {...register("customer_person_type")}
              className="w-full rounded-md border border-input bg-background px-3 py-2.5 text-sm outline-none transition-colors focus:ring-2 focus:ring-ring/50"
            >
              <option value="">Seleccionar...</option>
              <option value="individual">Persona física</option>
              <option value="empresa">Empresa</option>
            </select>

            {errors.customer_person_type && (
              <p className="text-xs text-destructive font-medium">
                {errors.customer_person_type.message}
              </p>
            )}
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="customer_iva_condition">
              Condición frente al IVA
            </Label>

            <select
              id="customer_iva_condition"
              {...register("customer_iva_condition")}
              className="w-full rounded-md border border-input bg-background px-3 py-2.5 text-sm outline-none transition-colors focus:ring-2 focus:ring-ring/50"
            >
              <option value="">Seleccionar...</option>
              <option value="consumidor_final">Consumidor Final</option>
              <option value="responsable_inscripto">
                Responsable Inscripto
              </option>
              <option value="monotributista">Monotributista</option>
              <option value="exento">Exento</option>
            </select>

            {errors.customer_iva_condition && (
              <p className="text-xs text-destructive font-medium">
                {errors.customer_iva_condition.message}
              </p>
            )}
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="space-y-1.5">
            <Label htmlFor="customer_tax_id">CUIT</Label>

            <input
              id="customer_tax_id"
              {...register("customer_tax_id")}
              placeholder="Ej: 20-12345678-9"
              inputMode="numeric"
              className="w-full rounded-md border border-input bg-background px-3 py-2.5 text-sm outline-none transition-colors focus:ring-2 focus:ring-ring/50"
            />

            {errors.customer_tax_id && (
              <p className="text-xs text-destructive font-medium">
                {errors.customer_tax_id.message}
              </p>
            )}
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="customer_dni">DNI</Label>

            <input
              id="customer_dni"
              {...register("customer_dni")}
              placeholder="Ej: 35123456"
              inputMode="numeric"
              className="w-full rounded-md border border-input bg-background px-3 py-2.5 text-sm outline-none transition-colors focus:ring-2 focus:ring-ring/50"
            />

            {errors.customer_dni && (
              <p className="text-xs text-destructive font-medium">
                {errors.customer_dni.message}
              </p>
            )}
          </div>
        </div>
      </div>

      <div className="space-y-1.5">
        <Label htmlFor="delivery_type">Método de entrega</Label>
        <select
          id="delivery_type"
          {...register("delivery_type")}
          className="w-full rounded-md border border-input bg-background px-3 py-2.5 text-sm outline-none transition-colors focus:ring-2 focus:ring-ring/50"
        >
          <option value="delivery">Envío a domicilio</option>
          <option value="pickup">Retiro en local</option>
        </select>
      </div>

      {isDelivery && (
        <div className="space-y-4 rounded-lg border bg-muted/40 p-4 animate-in fade-in duration-300">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-1.5">
              <Label htmlFor="delivery_address">Calle y número</Label>
              <input
                id="delivery_address"
                {...register("delivery_address")}
                placeholder="Ej: Av. Rivadavia 1234"
                className="w-full rounded-md border border-input bg-background px-3 py-2.5 text-sm outline-none transition-colors focus:ring-2 focus:ring-ring/50"
              />
              {errors.delivery_address && (
                <p className="text-xs text-destructive font-medium">
                  {errors.delivery_address.message}
                </p>
              )}
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="delivery_city">Ciudad / Localidad</Label>
              <input
                id="delivery_city"
                {...register("delivery_city")}
                placeholder="Ej: Mercedes"
                className="w-full rounded-md border border-input bg-background px-3 py-2.5 text-sm outline-none transition-colors focus:ring-2 focus:ring-ring/50"
              />
              {errors.delivery_city && (
                <p className="text-xs text-destructive font-medium">
                  {errors.delivery_city.message}
                </p>
              )}
            </div>
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="delivery_reference">Referencia (opcional)</Label>
            <input
              id="delivery_reference"
              {...register("delivery_reference")}
              placeholder="Ej: Portón blanco, entre calles..."
              className="w-full rounded-md border border-input bg-background px-3 py-2.5 text-sm outline-none transition-colors focus:ring-2 focus:ring-ring/50"
            />
          </div>
        </div>
      )}

      <div className="space-y-1.5 rounded-lg border bg-muted/40 p-4">
        <Label
          htmlFor="preferred_delivery_date"
          className="flex items-center gap-2"
        >
          <CalendarDays className="h-4 w-4 text-muted-foreground" />
          Fecha de entrega preferida
        </Label>
        <p className="text-xs text-muted-foreground">
          Elegí cuándo querés recibir tu pedido (hasta 30 días desde hoy).
        </p>
        <input
          id="preferred_delivery_date"
          type="date"
          min={todayStr}
          max={maxDateStr}
          {...register("preferred_delivery_date")}
          className="w-full rounded-md border border-input bg-background px-3 py-2.5 text-sm outline-none transition-colors focus:ring-2 focus:ring-ring/50"
        />
        {errors.preferred_delivery_date && (
          <p className="text-xs text-destructive font-medium">
            {errors.preferred_delivery_date.message}
          </p>
        )}
      </div>

      <div className="space-y-4 rounded-lg border bg-muted/40 p-4">
        <div>
          <h3 className="text-sm font-semibold">Tipo de documento</h3>
          <p className="mt-1 text-xs text-muted-foreground">
            Elegí qué documento querés solicitar para este pedido.
          </p>
        </div>

        <div className="space-y-1.5">
          <Label htmlFor="document_type">Documento</Label>

          <select
            id="document_type"
            {...register("document_type")}
            className="w-full rounded-md border border-input bg-background px-3 py-2.5 text-sm outline-none transition-colors focus:ring-2 focus:ring-ring/50"
          >
            <option value="">Seleccionar...</option>
            <option value="sales_invoice">Remito</option>
            <option value="sales_quote">Presupuesto</option>
          </select>

          {errors.document_type && (
            <p className="text-xs text-destructive font-medium">
              {errors.document_type.message}
            </p>
          )}
        </div>
      </div>

      <div className="rounded-lg border border-yellow-500/30 bg-yellow-500/5 p-4">
        <div className="space-y-3">
          <div>
            <h3 className="text-sm font-semibold">Verificación de edad</h3>

            <p className="text-xs text-muted-foreground">
              Este pedido contiene productos cuya venta está restringida a
              mayores de 18 años.
            </p>
          </div>

          <div className="flex items-start gap-3">
            <input
              id="age_confirmed"
              type="checkbox"
              {...register("age_confirmed")}
              className="mt-0.5 h-4 w-4 rounded border-input"
            />

            <Label
              htmlFor="age_confirmed"
              className="cursor-pointer text-sm leading-5"
            >
              Confirmo que soy mayor de 18 años.
            </Label>
          </div>

          {errors.age_confirmed && (
            <p className="text-xs text-destructive font-medium">
              {errors.age_confirmed.message}
            </p>
          )}
        </div>
      </div>

      <button
        type="submit"
        disabled={isPending}
        className="w-full rounded-md bg-foreground px-6 py-4 text-sm font-bold text-background transition-opacity hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {isPending ? "Procesando..." : `Confirmar pedido · $${totalLabel}`}
      </button>
    </form>
  );
}
