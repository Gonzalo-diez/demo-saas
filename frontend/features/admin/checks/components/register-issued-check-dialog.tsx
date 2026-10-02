"use client";

import { useState, type ReactNode } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { toast } from "sonner";
import { ArrowUpRight } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Dialog,
  DialogContent,
  DialogDescription,
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
  registerIssuedCheckSchema,
  type RegisterIssuedCheckFormInput,
  type RegisterIssuedCheckFormValues,
} from "@/features/admin/checks/schemas/check-schema";
import { useRegisterIssuedCheck } from "@/features/admin/checks/hooks/use-register-issued-check";
import { useSuppliers } from "@/features/admin/suppliers/hooks/use-suppliers";

/**
 * Contexto opcional para abrir el diálogo desde una fila de Cuenta corriente:
 * el proveedor y el remito de compra ya se conocen. Los cheques emitidos solo
 * se imputan a remitos de compra (no a presupuestos).
 */
export type IssuedCheckTarget = {
  supplier: { id: number; name: string };
  document?: {
    id: number;
    number: string;
    /** Deuda pendiente del remito (tope de lo que se imputa). */
    balance: number;
  };
};

type RegisterIssuedCheckDialogProps = {
  /** Botón que abre el diálogo. Por defecto: "Cheque emitido". */
  trigger?: ReactNode;
  target?: IssuedCheckTarget;
};

const emptyDefaults: RegisterIssuedCheckFormInput = {
  supplier_id: 0,
  check_number: "",
  bank_name: "",
  drawer_name: "",
  amount: 0,
  issue_date: "",
  payment_date: "",
  due_date: "",
  notes: "",
  allocate: false,
  allocation_invoice_id: undefined,
  allocation_amount: undefined,
};

function formatMoney(value: number) {
  return new Intl.NumberFormat("es-AR", {
    style: "currency",
    currency: "ARS",
  }).format(Number.isNaN(value) ? 0 : value);
}

function roundMoney(value: number) {
  return Math.round(value * 100) / 100;
}

function SupplierSelect({
  value,
  onChange,
  error,
}: {
  value: number;
  onChange: (supplierId: number) => void;
  error?: string;
}) {
  const suppliersQuery = useSuppliers({ page: 1, page_size: 20, search: "", status: "active" });
  const suppliers = suppliersQuery.data?.suppliers ?? [];

  return (
    <div className="space-y-1.5">
      <label className="text-sm font-medium">Proveedor</label>
      <Select
        value={value > 0 ? String(value) : "__empty__"}
        onValueChange={(next) => onChange(next === "__empty__" ? 0 : Number(next))}
      >
        <SelectTrigger>
          <SelectValue placeholder="Seleccionar proveedor" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="__empty__">Seleccionar</SelectItem>
          {suppliers.map((supplier) => (
            <SelectItem key={supplier.id} value={String(supplier.id)}>
              {supplier.name}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
      {error && <p className="text-sm text-destructive">{error}</p>}
    </div>
  );
}

export function IssuedCheckForm({
  target,
  onDone,
}: {
  target?: IssuedCheckTarget;
  onDone: () => void;
}) {
  const registerIssuedCheck = useRegisterIssuedCheck();
  const targetDocument = target?.document;

  const {
    handleSubmit,
    register,
    setValue,
    watch,
    formState: { errors },
  } = useForm<RegisterIssuedCheckFormInput, undefined, RegisterIssuedCheckFormValues>({
    resolver: zodResolver(registerIssuedCheckSchema),
    defaultValues: {
      ...emptyDefaults,
      supplier_id: target?.supplier.id ?? 0,
      amount: targetDocument ? roundMoney(targetDocument.balance) : 0,
    },
  });

  const supplierId = Number(watch("supplier_id") ?? 0);
  const allocate = watch("allocate");
  const checkAmount = Number(watch("amount") ?? 0);
  const unallocated = targetDocument
    ? roundMoney(checkAmount - targetDocument.balance)
    : 0;

  async function onSubmit(data: RegisterIssuedCheckFormValues) {
    const allocations = targetDocument
      ? [
          {
            invoice_id: targetDocument.id,
            amount: roundMoney(Math.min(data.amount, targetDocument.balance)),
          },
        ]
      : data.allocate && data.allocation_invoice_id && data.allocation_amount
        ? [{ invoice_id: data.allocation_invoice_id, amount: data.allocation_amount }]
        : null;

    try {
      await registerIssuedCheck.mutateAsync({
        supplierId: data.supplier_id,
        data: {
          check_number: data.check_number,
          bank_name: data.bank_name || null,
          drawer_name: data.drawer_name || null,
          amount: data.amount,
          issue_date: data.issue_date,
          payment_date: data.payment_date,
          due_date: data.due_date,
          notes: data.notes || null,
          allocations,
        },
      });

      toast.success("Cheque emitido registrado. Queda pendiente hasta acreditarlo.", {
        position: "top-right",
        duration: 4000,
      });

      onDone();
    } catch (error) {
      toast.error(
        error instanceof Error ? error.message : "No se pudo registrar el cheque",
        { position: "top-right", duration: 4000 }
      );
    }
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      {target ? (
        <div className="space-y-1.5">
          <label className="text-sm font-medium">Proveedor</label>
          <p className="rounded-md border bg-muted/30 px-3 py-2 text-sm">{target.supplier.name}</p>
        </div>
      ) : (
        <SupplierSelect
          value={supplierId}
          onChange={(next) => setValue("supplier_id", next, { shouldValidate: true })}
          error={errors.supplier_id?.message}
        />
      )}

      <div className="grid gap-4 sm:grid-cols-2">
        <div className="space-y-1.5">
          <label className="text-sm font-medium">Número de cheque</label>
          <Input {...register("check_number")} placeholder="00012345" />
          {errors.check_number && (
            <p className="text-sm text-destructive">{errors.check_number.message}</p>
          )}
        </div>

        <div className="space-y-1.5">
          <label className="text-sm font-medium">Monto</label>
          <Input type="number" min={0} step="0.01" {...register("amount")} />
          {errors.amount && (
            <p className="text-sm text-destructive">{errors.amount.message}</p>
          )}
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <div className="space-y-1.5">
          <label className="text-sm font-medium">Banco</label>
          <Input {...register("bank_name")} placeholder="Banco emisor" />
        </div>

        <div className="space-y-1.5">
          <label className="text-sm font-medium">Titular / librador</label>
          <Input {...register("drawer_name")} placeholder="Nombre del librador" />
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        <div className="space-y-1.5">
          <label className="text-sm font-medium">Emisión</label>
          <Input type="date" {...register("issue_date")} />
          {errors.issue_date && (
            <p className="text-sm text-destructive">{errors.issue_date.message}</p>
          )}
        </div>

        <div className="space-y-1.5">
          <label className="text-sm font-medium">Fecha de pago</label>
          <Input type="date" {...register("payment_date")} />
          {errors.payment_date && (
            <p className="text-sm text-destructive">{errors.payment_date.message}</p>
          )}
        </div>

        <div className="space-y-1.5">
          <label className="text-sm font-medium">Vencimiento</label>
          <Input type="date" {...register("due_date")} />
          {errors.due_date && (
            <p className="text-sm text-destructive">{errors.due_date.message}</p>
          )}
        </div>
      </div>

      <div className="space-y-1.5">
        <label className="text-sm font-medium">Notas</label>
        <Textarea {...register("notes")} placeholder="Notas opcionales" />
      </div>

      {targetDocument ? (
        <div className="space-y-1 rounded-xl border bg-muted/30 p-3 text-sm">
          <p>
            Se imputa al remito de compra{" "}
            <span className="font-medium">#{targetDocument.number}</span> (deuda pendiente{" "}
            {formatMoney(targetDocument.balance)}).
          </p>
          <p className="text-xs text-muted-foreground">
            La deuda se descuenta recién cuando acredites el cheque.
          </p>
          {unallocated > 0 && (
            <p className="text-xs text-amber-700">
              El cheque supera la deuda: {formatMoney(unallocated)} quedan sin imputar a este
              remito.
            </p>
          )}
        </div>
      ) : (
        <div className="space-y-3 rounded-xl border p-3">
          <div className="flex items-center gap-2">
            <Checkbox
              id="allocate-issued-check"
              checked={!!allocate}
              onCheckedChange={(checked) =>
                setValue("allocate", checked === true, { shouldValidate: true })
              }
            />
            <label htmlFor="allocate-issued-check" className="text-sm font-medium">
              Imputar a un remito de compra puntual (opcional)
            </label>
          </div>

          {allocate && (
            <div className="grid gap-3 sm:grid-cols-2">
              <div className="space-y-1.5">
                <label className="text-xs font-medium">Número de remito (ID)</label>
                <Input type="number" min={1} {...register("allocation_invoice_id")} />
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-medium">Monto imputado</label>
                <Input type="number" min={0} step="0.01" {...register("allocation_amount")} />
              </div>

              {errors.allocation_invoice_id && (
                <p className="text-sm text-destructive sm:col-span-2">
                  {errors.allocation_invoice_id.message}
                </p>
              )}
              {errors.allocation_amount && (
                <p className="text-sm text-destructive sm:col-span-2">
                  {errors.allocation_amount.message}
                </p>
              )}
            </div>
          )}
        </div>
      )}

      <div className="flex justify-end">
        <Button type="submit" disabled={registerIssuedCheck.isPending}>
          {registerIssuedCheck.isPending ? "Guardando..." : "Registrar cheque"}
        </Button>
      </div>
    </form>
  );
}

export function RegisterIssuedCheckDialog({
  trigger,
  target,
}: RegisterIssuedCheckDialogProps) {
  const [open, setOpen] = useState(false);

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        {trigger ?? (
          <Button variant="outline">
            <ArrowUpRight className="mr-2 h-4 w-4" />
            Cheque emitido
          </Button>
        )}
      </DialogTrigger>

      <DialogContent className="max-h-[90vh] overflow-y-auto sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>Registrar cheque emitido</DialogTitle>
          <DialogDescription>
            Cheque propio emitido a un proveedor como pago. Queda pendiente y no afecta la deuda
            hasta que lo acredités.
          </DialogDescription>
        </DialogHeader>

        {/* El formulario solo se monta con el diálogo abierto: al cerrar se descarta su estado */}
        <IssuedCheckForm target={target} onDone={() => setOpen(false)} />
      </DialogContent>
    </Dialog>
  );
}
