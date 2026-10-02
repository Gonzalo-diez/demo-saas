import React from "react";
import { useQuery } from "@tanstack/react-query";
import { Badge } from "@/components/ui/badge";
import { Clock, ArrowDownRight, ArrowUpRight } from "lucide-react";
import { getDocumentPendingChecksApi } from "@/features/admin/checks/apis/check-api";

export interface DocumentPendingChecksBadgeProps {
  documentType: "sales_invoice" | "sales_quote" | "purchase_invoice" | "purchase_quote";
  documentId: number;
}

const VARIANT_CONFIG = {
  sales: {
    badgeClass: "bg-emerald-50 text-emerald-800 border-emerald-200 hover:bg-emerald-100",
    iconClass: "text-emerald-600",
    Icon: ArrowDownRight,
    label: "Cobro en cartera:",
  },
  purchases: {
    badgeClass: "bg-indigo-50 text-indigo-800 border-indigo-200 hover:bg-indigo-100",
    iconClass: "text-indigo-600",
    Icon: ArrowUpRight,
    label: "Pago diferido:",
  },
};

export function DocumentPendingChecksBadge({
  documentType,
  documentId,
}: DocumentPendingChecksBadgeProps) {
  // La key cuelga de ["checks"]: registrar, depositar, acreditar o rechazar un
  // cheque (que invalidan esa key) refresca este badge sin recargar la página.
  const { data } = useQuery({
    queryKey: ["checks", "document-pending", documentType, documentId],
    queryFn: () => getDocumentPendingChecksApi(documentType, documentId),
  });

  if (!data) return null;
  const pendingAmount = Number(data.pending_amount);
  if (isNaN(pendingAmount) || pendingAmount <= 0) return null;

  const formattedAmount = new Intl.NumberFormat("es-AR", {
    style: "currency",
    currency: "ARS",
  }).format(pendingAmount);

  const isSale = documentType.startsWith("sales");
  const config = isSale ? VARIANT_CONFIG.sales : VARIANT_CONFIG.purchases;
  const { Icon } = config;

  return (
    <Badge
      variant="outline"
      title={isSale ? "Cheques recibidos pendientes de acreditación" : "Cheques emitidos pendientes de débito"}
      className={`gap-1.5 py-1 ${config.badgeClass}`}
    >
      <div className="relative flex items-center justify-center">
        <Clock className={`w-3.5 h-3.5 ${config.iconClass}`} strokeWidth={2} />
        <div className="absolute -bottom-1 -right-1 bg-white rounded-full">
          <Icon className={`w-2.5 h-2.5 ${config.iconClass}`} strokeWidth={3} />
        </div>
      </div>
      <span className="font-normal">{config.label}</span>
      <span className="font-bold">{formattedAmount}</span>
    </Badge>
  );
}