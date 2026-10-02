"use client";

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";

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
  paymentMethodOptions,
  registerPaymentSchema,
  type RegisterPaymentFormValues,
} from "@/features/admin/account-movements/schemas/account-movement-schema";
import { useRegisterSupplierPayment } from "@/features/admin/account-movements/hooks/use-register-supplier-payment";
import { RegisterIssuedCheckDialog } from "@/features/admin/checks/components/register-issued-check-dialog";
import type { PaymentMethod } from "@/features/admin/account-movements/types";

type RegisterSupplierPaymentFormProps = {
  supplierId: number;
  onSuccess?: () => void;
};

export function RegisterSupplierPaymentForm({
  supplierId,
  onSuccess,
}: RegisterSupplierPaymentFormProps) {
  const registerPayment = useRegisterSupplierPayment();

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    reset,
    formState: { errors },
  } = useForm<
    z.input<typeof registerPaymentSchema>,
    unknown,
    z.output<typeof registerPaymentSchema>
  >({
    resolver: zodResolver(registerPaymentSchema),
    defaultValues: {
      amount: undefined,
      payment_method: undefined,
      notes: "",
    },
  });

  const paymentMethod = watch("payment_method");

  async function onSubmit(data: RegisterPaymentFormValues) {
    try {
      await registerPayment.mutateAsync({
        supplierId,
        data: {
          amount: data.amount,
          payment_method: data.payment_method as PaymentMethod,
          notes: data.notes || null,
        },
      });

      reset();
      onSuccess?.();
    } catch {
      // el error ya se muestra vía toast en el hook
    }
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <div className="grid gap-4 sm:grid-cols-2">
        <div className="space-y-1.5">
          <label className="text-sm font-medium">Monto</label>
          <Input
            type="number"
            step="0.01"
            min="0"
            placeholder="0.00"
            {...register("amount")}
          />
          {errors.amount && (
            <p className="text-sm text-destructive">{errors.amount.message}</p>
          )}
        </div>

        <div className="space-y-1.5">
          <label className="text-sm font-medium">Método de pago</label>
          <Select
            value={paymentMethod ?? ""}
            onValueChange={(value) =>
              setValue("payment_method", value as RegisterPaymentFormValues["payment_method"], {
                shouldValidate: true,
                shouldDirty: true,
              })
            }
          >
            <SelectTrigger>
              <SelectValue placeholder="Seleccionar" />
            </SelectTrigger>
            <SelectContent>
              {paymentMethodOptions.map((option) => (
                <SelectItem key={option.value} value={option.value}>
                  {option.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          {errors.payment_method && (
            <p className="text-sm text-destructive">
              {errors.payment_method.message}
            </p>
          )}
        </div>
      </div>

      <div className="space-y-1.5">
        <label className="text-sm font-medium">Notas (opcional)</label>
        <Textarea rows={2} {...register("notes")} />
        {errors.notes && (
          <p className="text-sm text-destructive">{errors.notes.message}</p>
        )}
      </div>

      <p className="text-xs text-muted-foreground">
        Este pago se aplica al saldo general del proveedor, sin imputarse a
        un remito puntual. Para saldar un remito específico, registrá el
        pago desde ese remito en la tabla de Remitos de compra.
      </p>

      <div className="flex items-center justify-between gap-2 rounded-lg border bg-muted/40 p-3">
        <p className="text-xs text-muted-foreground">
          ¿Paga con cheque emitido? Solo se puede imputar a remitos de
          compra — registralo desde el alta de cheque.
        </p>
        <RegisterIssuedCheckDialog />
      </div>

      <div className="flex justify-end">
        <Button type="submit" disabled={registerPayment.isPending}>
          {registerPayment.isPending ? "Guardando..." : "Registrar pago"}
        </Button>
      </div>
    </form>
  );
}