"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { CircleDollarSign } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
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
import { useRegisterClientPayment } from "@/features/admin/account-movements/hooks/use-register-client-payment";
import { useRegisterSalesInvoicePayment } from "@/features/admin/account-movements/hooks/use-sales-invoice-payments";
import { formatCurrency } from "@/features/admin/account-movements/components/account-movement-helpers";
import { RegisterReceivedCheckDialog } from "@/features/admin/checks/components/register-received-check-dialog";
import type { PaymentMethod } from "@/features/admin/account-movements/types";
import type { SalesInvoice } from "@/features/admin/sales-invoices/types";

type RegisterSalesInvoicePaymentDialogProps = {
  invoice: SalesInvoice;
};

export function RegisterSalesInvoicePaymentDialog({
  invoice,
}: RegisterSalesInvoicePaymentDialogProps) {
  const [open, setOpen] = useState(false);

  const registerClientPayment = useRegisterClientPayment();
  const registerOnlinePayment = useRegisterSalesInvoicePayment();

  const isPending =
    registerClientPayment.isPending || registerOnlinePayment.isPending;

  const total = Number(invoice.total_amount ?? 0);
  const paid = Number(invoice.paid_amount ?? 0);
  const remaining = Math.max(total - paid, 0);

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
      amount: remaining,
      payment_method: undefined,
      notes: "",
    },
  });

  const paymentMethod = watch("payment_method");

  async function onSubmit(data: RegisterPaymentFormValues) {
    try {
      if (invoice.client_id) {
        await registerClientPayment.mutateAsync({
          clientId: invoice.client_id,
          data: {
            amount: data.amount,
            payment_method: data.payment_method as PaymentMethod,
            notes: data.notes || null,
            allocations: [{ invoice_id: invoice.id, amount: data.amount }],
          },
        });
      } else {
        await registerOnlinePayment.mutateAsync({
          salesInvoiceId: invoice.id,
          data: {
            amount: data.amount,
            payment_method: data.payment_method as PaymentMethod,
            notes: data.notes || null,
          },
        });
      }

      reset();
      setOpen(false);
    } catch {
      // el error ya se muestra vía toast en el hook
    }
  }

  if (invoice.status !== "confirmed" || invoice.payment_status === "paid") {
    return null;
  }

  return (
    <Dialog
      open={open}
      onOpenChange={(value) => {
        setOpen(value);
        if (value) reset({ amount: remaining, payment_method: undefined, notes: "" });
      }}
    >
      <DialogTrigger asChild>
        <Button type="button" variant="outline" size="sm">
          <CircleDollarSign className="mr-2 h-4 w-4" />
          Registrar cobro
        </Button>
      </DialogTrigger>

      <DialogContent className="px-4 sm:max-w-md sm:px-6">
        <DialogHeader>
          <DialogTitle>Registrar cobro — Remito {invoice.invoice_number}</DialogTitle>
          <DialogDescription>
            Saldo pendiente: {formatCurrency(String(remaining))}
            {invoice.client_id
              ? " · Se imputa a la cuenta corriente del cliente."
              : " · Cobro contra entrega (no genera cuenta corriente)."}
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div className="space-y-1.5">
            <label className="text-sm font-medium">Monto</label>
            <Input
              type="number"
              step="0.01"
              min="0"
              max={remaining || undefined}
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
                setValue(
                  "payment_method",
                  value as RegisterPaymentFormValues["payment_method"],
                  { shouldValidate: true, shouldDirty: true }
                )
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

          <div className="space-y-1.5">
            <label className="text-sm font-medium">Notas (opcional)</label>
            <Textarea rows={2} {...register("notes")} />
          </div>

          <div className="flex items-center justify-between gap-2 rounded-lg border bg-muted/40 p-3">
            <p className="text-xs text-muted-foreground">
              ¿Cobra con cheque? El saldo recién se mueve cuando se acredita.
            </p>
            <RegisterReceivedCheckDialog />
          </div>

          <DialogFooter>
            <Button type="submit" disabled={isPending}>
              {isPending ? "Guardando..." : "Registrar cobro"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}