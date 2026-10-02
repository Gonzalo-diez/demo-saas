"use client";

import { useState, type ReactNode } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { toast } from "sonner";
import { ArrowDownLeft } from "lucide-react";

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
  registerReceivedCheckSchema,
  type RegisterReceivedCheckFormInput,
  type RegisterReceivedCheckFormValues,
} from "@/features/admin/checks/schemas/check-schema";
import { useRegisterReceivedCheck } from "@/features/admin/checks/hooks/use-register-received-check";
import { useClients } from "@/features/admin/clients/hooks/use-clients";

/**
 * Contexto opcional para abrir el diálogo desde una fila de Cuenta corriente:
 * el cliente y el documento ya se conocen, así que no se vuelven a elegir ni
 * hay que tipear el ID del remito/presupuesto a mano.
 */
export type ReceivedCheckTarget = {
  client: { id: number; name: string };
  document?: {
    type: "sales_invoice" | "sales_quote";
    id: number;
    number: string;
    /** Saldo pendiente del documento (tope de lo que se imputa). */
    balance: number;
  };
};

type RegisterReceivedCheckDialogProps = {
  /** Botón que abre el diálogo. Por defecto: "Cheque recibido". */
  trigger?: ReactNode;
  target?: ReceivedCheckTarget;
};

const emptyDefaults: RegisterReceivedCheckFormInput = {
  client_id: 0,
  check_number: "",
  bank_name: "",
  drawer_name: "",
  amount: 0,
  issue_date: "",
  payment_date: "",
  due_date: "",
  notes: "",
  allocate: false,
  allocation_document_type: "sales_invoice",
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

function ClientSelect({
  value,
  onChange,
  error,
}: {
  value: number;
  onChange: (clientId: number) => void;
  error?: string;
}) {
  const clientsQuery = useClients({
    page: 1,
    page_size: 20,
    search: "",
    status: "active",
    sort: "name",
  });
  const clients = clientsQuery.data?.clients ?? [];

  return (
    <div className="space-y-1.5">
      <label className="text-sm font-medium">Cliente</label>
      <Select
        value={value > 0 ? String(value) : "__empty__"}
        onValueChange={(next) => onChange(next === "__empty__" ? 0 : Number(next))}
      >
        <SelectTrigger>
          <SelectValue placeholder="Seleccionar cliente" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="__empty__">Seleccionar</SelectItem>
          {clients.map((client) => (
            <SelectItem key={client.id} value={String(client.id)}>
              {client.name}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
      {error && <p className="text-sm text-destructive">{error}</p>}
    </div>
  );
}

export function ReceivedCheckForm({
  target,
  onDone,
}: {
  target?: ReceivedCheckTarget;
  onDone: () => void;
}) {
  const registerReceivedCheck = useRegisterReceivedCheck();
  const targetDocument = target?.document;

  const {
    handleSubmit,
    register,
    setValue,
    watch,
    formState: { errors },
  } = useForm<RegisterReceivedCheckFormInput, undefined, RegisterReceivedCheckFormValues>({
    resolver: zodResolver(registerReceivedCheckSchema),
    defaultValues: {
      ...emptyDefaults,
      client_id: target?.client.id ?? 0,
      amount: targetDocument ? roundMoney(targetDocument.balance) : 0,
    },
  });

  const clientId = Number(watch("client_id") ?? 0);
  const allocate = watch("allocate");
  const allocationDocumentType = watch("allocation_document_type");
  const checkAmount = Number(watch("amount") ?? 0);
  const unallocated = targetDocument
    ? roundMoney(checkAmount - targetDocument.balance)
    : 0;

  async function onSubmit(data: RegisterReceivedCheckFormValues) {
    const allocations = targetDocument
      ? [
          {
            invoice_id: targetDocument.id,
            amount: roundMoney(Math.min(data.amount, targetDocument.balance)),
            document_type: targetDocument.type,
          },
        ]
      : data.allocate && data.allocation_invoice_id && data.allocation_amount
        ? [
            {
              invoice_id: data.allocation_invoice_id,
              amount: data.allocation_amount,
              document_type: data.allocation_document_type ?? "sales_invoice",
            },
          ]
        : null;

    try {
      await registerReceivedCheck.mutateAsync({
        clientId: data.client_id,
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

      toast.success("Cheque recibido registrado. Queda pendiente hasta acreditarlo.", {
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
          <label className="text-sm font-medium">Cliente</label>
          <p className="rounded-md border bg-muted/30 px-3 py-2 text-sm">{target.client.name}</p>
        </div>
      ) : (
        <ClientSelect
          value={clientId}
          onChange={(next) => setValue("client_id", next, { shouldValidate: true })}
          error={errors.client_id?.message}
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
            Se imputa al{" "}
            <span className="font-medium">
              {targetDocument.type === "sales_quote" ? "presupuesto" : "remito"} #
              {targetDocument.number}
            </span>{" "}
            (saldo pendiente {formatMoney(targetDocument.balance)}).
          </p>
          <p className="text-xs text-muted-foreground">
            El saldo se descuenta recién cuando acredites el cheque.
            {targetDocument.type === "sales_quote" &&
              " Los presupuestos solo admiten cobros si nacieron de un pedido y están aprobados."}
          </p>
          {unallocated > 0 && (
            <p className="text-xs text-amber-700">
              El cheque supera el saldo: {formatMoney(unallocated)} quedan sin imputar a este
              documento.
            </p>
          )}
        </div>
      ) : (
        <div className="space-y-3 rounded-xl border p-3">
          <div className="flex items-center gap-2">
            <Checkbox
              id="allocate-received-check"
              checked={!!allocate}
              onCheckedChange={(checked) =>
                setValue("allocate", checked === true, { shouldValidate: true })
              }
            />
            <label htmlFor="allocate-received-check" className="text-sm font-medium">
              Imputar a un remito o presupuesto puntual (opcional)
            </label>
          </div>

          {allocate && (
            <div className="grid gap-3 sm:grid-cols-3">
              <div className="space-y-1.5">
                <label className="text-xs font-medium">Tipo de documento</label>
                <Select
                  value={allocationDocumentType ?? "sales_invoice"}
                  onValueChange={(value) =>
                    setValue(
                      "allocation_document_type",
                      value as "sales_invoice" | "sales_quote",
                      { shouldValidate: true }
                    )
                  }
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="sales_invoice">Remito de venta</SelectItem>
                    <SelectItem value="sales_quote">Presupuesto de venta</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-medium">Número (ID)</label>
                <Input type="number" min={1} {...register("allocation_invoice_id")} />
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-medium">Monto imputado</label>
                <Input type="number" min={0} step="0.01" {...register("allocation_amount")} />
              </div>

              {errors.allocation_invoice_id && (
                <p className="text-sm text-destructive sm:col-span-3">
                  {errors.allocation_invoice_id.message}
                </p>
              )}
              {errors.allocation_amount && (
                <p className="text-sm text-destructive sm:col-span-3">
                  {errors.allocation_amount.message}
                </p>
              )}
            </div>
          )}
        </div>
      )}

      <div className="flex justify-end">
        <Button type="submit" disabled={registerReceivedCheck.isPending}>
          {registerReceivedCheck.isPending ? "Guardando..." : "Registrar cheque"}
        </Button>
      </div>
    </form>
  );
}

export function RegisterReceivedCheckDialog({
  trigger,
  target,
}: RegisterReceivedCheckDialogProps) {
  const [open, setOpen] = useState(false);

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        {trigger ?? (
          <Button variant="outline">
            <ArrowDownLeft className="mr-2 h-4 w-4" />
            Cheque recibido
          </Button>
        )}
      </DialogTrigger>

      <DialogContent className="max-h-[90vh] overflow-y-auto sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>Registrar cheque recibido</DialogTitle>
          <DialogDescription>
            Cheque de un cliente como cobro. Queda pendiente y no afecta el saldo hasta que lo
            acredités.
          </DialogDescription>
        </DialogHeader>

        {/* El formulario solo se monta con el diálogo abierto: al cerrar se descarta su estado */}
        <ReceivedCheckForm target={target} onDone={() => setOpen(false)} />
      </DialogContent>
    </Dialog>
  );
}
