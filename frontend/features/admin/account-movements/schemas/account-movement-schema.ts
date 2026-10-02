import { z } from "zod";

export const paymentMethodOptions = [
  { value: "efectivo", label: "Efectivo" },
  { value: "debito", label: "Débito" },
  { value: "credito", label: "Crédito" },
  { value: "otro", label: "Otro" },
] as const;

export const registerPaymentSchema = z.object({
  amount: z.coerce
    .number({ message: "Ingresá un monto válido" })
    .positive("El monto debe ser mayor a 0"),
  payment_method: z.enum(
    ["efectivo", "debito", "credito", "otro"],
    { message: "Seleccioná un método de pago" }
  ),
  notes: z.string().max(1000, "Máximo 1000 caracteres").optional().or(z.literal("")),
});

export type RegisterPaymentFormValues = z.infer<typeof registerPaymentSchema>;