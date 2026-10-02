import { Badge } from "@/components/ui/badge";
import {
  formatCurrency,
  formatDateTime,
} from "@/features/admin/account-movements/components/account-movement-helpers";
import type {
  LedgerPaymentEntry,
  LedgerProductLine,
} from "@/features/admin/account-ledger/types";

export { formatCurrency, formatDateTime };

/**
 * Label de método de pago propio de esta feature: el backend del ledger
 * usa efectivo/debito/credito/cheque/otro (ver ALLOWED_PAYMENT_METHODS),
 * que NO coincide con el getPaymentMethodLabel de account-movements
 * (ese es de efectivo/transferencia/cheque/tarjeta/mercado_pago/otro).
 * No reusar ese helper acá: "debito"/"credito" caían en su default "-".
 */
export function getPaymentMethodLabel(method: string | null) {
  switch (method) {
    case "efectivo":
      return "Efectivo";
    case "debito":
      return "Débito";
    case "credito":
      return "Crédito";
    case "cheque":
      return "Cheque";
    case "otro":
      return "Otro";
    default:
      return method || "-";
  }
}

export function formatDateOnly(value: string) {
  const date = new Date(`${value}T00:00:00`);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat("es-AR", { dateStyle: "short" }).format(date);
}

export function LedgerPaymentStatusBadge({ status }: { status: string }) {
  const config: Record<string, { label: string; className: string }> = {
    pending: {
      label: "Deuda",
      className: "bg-destructive/15 text-destructive hover:bg-destructive/15",
    },
    partial: {
      label: "Parcial",
      className: "bg-amber-500/15 text-amber-600 hover:bg-amber-500/15",
    },
    paid: {
      label: "Pagado",
      className: "bg-brand-muted text-brand hover:bg-brand-muted",
    },
  };

  const { label, className } = config[status] ?? { label: status, className: "" };

  return <Badge className={className}>{label}</Badge>;
}

export function SalesTypeBadge({ salesType }: { salesType: string }) {
  const config: Record<string, { label: string; className: string }> = {
    B2B: {
      label: "B2B",
      className: "bg-slate-500/15 text-slate-600 hover:bg-slate-500/15",
    },
    ONLINE: {
      label: "Online",
      className: "bg-sky-500/15 text-sky-600 hover:bg-sky-500/15",
    },
  };

  const { label, className } = config[salesType] ?? {
    label: salesType,
    className: "",
  };

  return <Badge className={className}>{label}</Badge>;
}

const documentTypeLabels: Record<string, string> = {
  sales_invoice: "Remito",
  sales_quote: "Presupuesto",
  purchase_invoice: "Remito",
  purchase_quote: "Presupuesto",
};

const documentTypeClassNames: Record<string, string> = {
  sales_invoice: "bg-chart-4/15 text-chart-4 hover:bg-chart-4/15",
  purchase_invoice: "bg-chart-4/15 text-chart-4 hover:bg-chart-4/15",
  sales_quote: "bg-chart-3/15 text-chart-3 hover:bg-chart-3/15",
  purchase_quote: "bg-chart-3/15 text-chart-3 hover:bg-chart-3/15",
};

/** Remito vs. presupuesto, para filas de venta o de compra por igual. */
export function DocumentTypeBadge({
  documentType,
  documentNumber,
}: {
  documentType: "sales_invoice" | "sales_quote" | "purchase_invoice" | "purchase_quote";
  documentNumber?: string;
}) {
  return (
    <div className="flex flex-col gap-1">
      <Badge className={documentTypeClassNames[documentType] ?? ""}>
        {documentTypeLabels[documentType] ?? documentType}
      </Badge>
      {documentNumber && (
        <span className="text-xs text-muted-foreground">{documentNumber}</span>
      )}
    </div>
  );
}

export function ProductLinesCell({
  products,
  showStock = false,
}: {
  products: LedgerProductLine[];
  showStock?: boolean;
}) {
  if (products.length === 0) {
    return <span className="text-muted-foreground">-</span>;
  }

  return (
    <ul className="space-y-1">
      {products.map((line, index) => (
        <li
          key={`${line.product_id ?? "sin-id"}-${index}`}
          className="flex items-center justify-between gap-2 whitespace-nowrap"
        >
          <span className="font-medium">{line.product_name}</span>
          <span className="text-muted-foreground">x{line.quantity}</span>
          {showStock && (
            <Badge variant="outline" className="ml-1 shrink-0">
              stock: {line.stock_current ?? "-"}
            </Badge>
          )}
        </li>
      ))}
    </ul>
  );
}

export function PaymentsCell({ payments }: { payments: LedgerPaymentEntry[] }) {
  if (payments.length === 0) {
    return <span className="text-muted-foreground">Sin pagos registrados</span>;
  }

  return (
    <ul className="space-y-1">
      {payments.map((payment, index) => (
        <li key={index} className="flex items-center justify-between gap-2 whitespace-nowrap">
          <Badge variant="outline">{getPaymentMethodLabel(payment.method)}</Badge>
          <span className="font-medium">{formatCurrency(payment.amount)}</span>
          <span className="text-muted-foreground text-[11px]">
            {formatDateTime(payment.date)}
          </span>
        </li>
      ))}
    </ul>
  );
}