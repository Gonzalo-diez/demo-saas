import { Badge } from "@/components/ui/badge";
import type { AccountMovementType } from "@/features/admin/account-movements/types";

export function formatCurrency(value: string | null) {
  const numericValue = Number(value ?? 0);

  return new Intl.NumberFormat("es-AR", {
    style: "currency",
    currency: "ARS",
    maximumFractionDigits: 2,
  }).format(Number.isNaN(numericValue) ? 0 : numericValue);
}

export function formatDateTime(value: string) {
  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return new Intl.DateTimeFormat("es-AR", {
    dateStyle: "short",
    timeStyle: "short",
  }).format(date);
}

export function getMovementTypeLabel(type: AccountMovementType) {
  switch (type) {
    case "invoice":
      return "Remito";
    case "invoice_reversal":
      return "Reversión de remito";
    case "payment":
      return "Cobro/Pago";
    case "credit_note":
      return "Nota de crédito";
    case "adjustment":
      return "Ajuste manual";
    default:
      return type;
  }
}

export function AccountMovementTypeBadge({
  type,
}: {
  type: AccountMovementType;
}) {
  const badgeClass = (() => {
    switch (type) {
      case "invoice":
        return "bg-destructive/15 text-destructive hover:bg-destructive/15";
      case "invoice_reversal":
      case "payment":
      case "credit_note":
        return "bg-brand-muted text-brand hover:bg-brand-muted";
      default:
        return "";
    }
  })();

  return (
    <Badge className={badgeClass}>{getMovementTypeLabel(type)}</Badge>
  );
}

export function getPaymentMethodLabel(method: string | null) {
  switch (method) {
    case "efectivo":
      return "Efectivo";
    case "transferencia":
      return "Transferencia";
    case "cheque":
      return "Cheque";
    case "tarjeta":
      return "Tarjeta";
    case "mercado_pago":
      return "Mercado Pago";
    case "otro":
      return "Otro";
    default:
      return "-";
  }
}

export function PaymentStatusBadge({ status }: { status: string }) {
  const config: Record<string, { label: string; className: string }> = {
    pending: {
      label: "Pendiente",
      className: "bg-destructive/15 text-destructive hover:bg-destructive/15",
    },
    partial: {
      label: "Parcial",
      className: "bg-amber-500/15 text-amber-600 hover:bg-amber-500/15",
    },
    paid: {
      label: "Pagada",
      className: "bg-brand-muted text-brand hover:bg-brand-muted",
    },
  };

  const { label, className } = config[status] ?? {
    label: status,
    className: "",
  };

  return <Badge className={className}>{label}</Badge>;
}