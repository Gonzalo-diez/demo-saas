"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import type { z } from "zod";

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
import { paymentMethodOptions } from "@/features/admin/account-movements/schemas/account-movement-schema";
import { formatCurrency } from "@/features/admin/account-ledger/components/ledger-helpers";
import type { LedgerCheckTarget } from "@/features/admin/account-ledger/components/ledger-check-target";
import { IssuedCheckForm } from "@/features/admin/checks/components/register-issued-check-dialog";
import { ReceivedCheckForm } from "@/features/admin/checks/components/register-received-check-dialog";
import { ledgerPaymentFormSchema } from "@/features/admin/account-ledger/schemas/account-ledger-schema";
import type { LedgerPaymentCreateInput, LedgerPaymentUpdateInput } from "@/features/admin/account-ledger/types";

// useForm necesita el tipo de ENTRADA del schema (antes de que z.coerce
// convierta el string del input a number); handleFormSubmit recibe el
// tipo de SALIDA ya validado y coercionado por el resolver.
type FormValues = z.input<typeof ledgerPaymentFormSchema>;
type FormOutput = z.output<typeof ledgerPaymentFormSchema>;

type PaymentFormDialogProps = {
  trigger: React.ReactNode;
  title: string;
  remaining: number;
  isPending: boolean;
  /**
   * Si se pasa (solo al agregar un pago), "Cheque" aparece como forma de pago:
   * al elegirlo el diálogo muestra los datos del cheque y lo registra imputado
   * a este documento, sin pasar por la página Cheques.
   */
  checkTarget?: LedgerCheckTarget;
  initialValues?: {
    amount: number;
    method: string;
    date: string;
    notes?: string | null;
  };
  onSubmit: (data: LedgerPaymentCreateInput | LedgerPaymentUpdateInput) => Promise<void>;
};

function toDatetimeLocalValue(isoDate: string) {
  const date = new Date(isoDate);
  if (Number.isNaN(date.getTime())) return "";
  const offset = date.getTimezoneOffset();
  const local = new Date(date.getTime() - offset * 60 * 1000);
  return local.toISOString().slice(0, 16);
}

export function PaymentFormDialog({
  trigger,
  title,
  remaining,
  isPending,
  checkTarget,
  initialValues,
  onSubmit,
}: PaymentFormDialogProps) {
  const [open, setOpen] = useState(false);

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    reset,
    formState: { errors },
  } = useForm<FormValues, unknown, FormOutput>({
    resolver: zodResolver(ledgerPaymentFormSchema),
    defaultValues: {
      amount: initialValues?.amount ?? remaining,
      method: (initialValues?.method as FormValues["method"]) ?? undefined,
      date: initialValues?.date ? toDatetimeLocalValue(initialValues.date) : "",
      notes: initialValues?.notes ?? "",
    },
  });

  const method = watch("method");
  const isCheck = !!checkTarget && method === "cheque";
  const methodOptions = checkTarget
    ? [...paymentMethodOptions, { value: "cheque", label: "Cheque" }]
    : paymentMethodOptions;

  async function handleFormSubmit(values: FormOutput) {
    await onSubmit({
      amount: values.amount,
      method: values.method,
      date: values.date ? new Date(values.date).toISOString() : null,
      notes: values.notes || null,
    });
    setOpen(false);
  }

  return (
    <Dialog
      open={open}
      onOpenChange={(value) => {
        setOpen(value);
        if (value) {
          reset({
            amount: initialValues?.amount ?? remaining,
            method: (initialValues?.method as FormValues["method"]) ?? undefined,
            date: initialValues?.date ? toDatetimeLocalValue(initialValues.date) : "",
            notes: initialValues?.notes ?? "",
          });
        }
      }}
    >
      <DialogTrigger asChild>{trigger}</DialogTrigger>

      <DialogContent
        className={`max-h-[90vh] overflow-y-auto px-4 sm:px-6 ${isCheck ? "sm:max-w-lg" : "sm:max-w-md"}`}
      >
        <DialogHeader>
          <DialogTitle>{title}</DialogTitle>
          {remaining > 0 && (
            <DialogDescription>
              Saldo pendiente: {formatCurrency(String(remaining))}
            </DialogDescription>
          )}
        </DialogHeader>

        <div className="space-y-4">
          <div className="space-y-1.5">
            <label className="text-sm font-medium">Método de pago</label>
            <Select
              value={method ?? ""}
              onValueChange={(value) =>
                setValue("method", value as FormValues["method"], {
                  shouldValidate: true,
                  shouldDirty: true,
                })
              }
            >
              <SelectTrigger>
                <SelectValue placeholder="Seleccionar" />
              </SelectTrigger>
              <SelectContent>
                {methodOptions.map((option) => (
                  <SelectItem key={option.value} value={option.value}>
                    {option.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            {errors.method && (
              <p className="text-sm text-destructive">{errors.method.message}</p>
            )}
          </div>

          {isCheck && checkTarget?.direction === "received" && (
            <ReceivedCheckForm
              target={{
                client: checkTarget.client,
                document: {
                  type: checkTarget.documentType,
                  id: checkTarget.documentId,
                  number: checkTarget.documentNumber,
                  balance: remaining,
                },
              }}
              onDone={() => setOpen(false)}
            />
          )}

          {isCheck && checkTarget?.direction === "issued" && (
            <IssuedCheckForm
              target={{
                supplier: checkTarget.supplier,
                document: {
                  id: checkTarget.documentId,
                  number: checkTarget.documentNumber,
                  balance: remaining,
                },
              }}
              onDone={() => setOpen(false)}
            />
          )}

          {!isCheck && (
            <form onSubmit={handleSubmit(handleFormSubmit)} className="space-y-4">
              <div className="space-y-1.5">
                <label className="text-sm font-medium">Monto</label>
                <Input type="number" step="0.01" min="0" {...register("amount")} />
                {errors.amount && (
                  <p className="text-sm text-destructive">{errors.amount.message}</p>
                )}
              </div>

              <div className="space-y-1.5">
                <label className="text-sm font-medium">Fecha (opcional)</label>
                <Input type="datetime-local" {...register("date")} />
              </div>

              <div className="space-y-1.5">
                <label className="text-sm font-medium">Notas (opcional)</label>
                <Textarea rows={2} {...register("notes")} />
              </div>

              <DialogFooter>
                <Button type="submit" disabled={isPending}>
                  {isPending ? "Guardando..." : "Guardar"}
                </Button>
              </DialogFooter>
            </form>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}