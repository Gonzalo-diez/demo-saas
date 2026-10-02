"use client";

import { Pencil, Plus } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { DocumentPendingChecksBadge } from "@/features/admin/checks/components/document-pending-checks-badge";
import { DeletePaymentButton } from "@/features/admin/account-ledger/components/delete-payment-button";
import {
  formatCurrency,
  formatDateTime,
  getPaymentMethodLabel,
} from "@/features/admin/account-ledger/components/ledger-helpers";
import type { LedgerCheckTarget } from "@/features/admin/account-ledger/components/ledger-check-target";
import { PaymentFormDialog } from "@/features/admin/account-ledger/components/payment-form-dialog";
import type {
  LedgerPaymentCreateInput,
  LedgerPaymentEntry,
  LedgerPaymentUpdateInput,
} from "@/features/admin/account-ledger/types";

export type { LedgerCheckTarget };

type EditablePaymentsCellProps = {
  payments: LedgerPaymentEntry[];
  checkTarget?: LedgerCheckTarget;
  remaining: number;
  isAdding: boolean;
  isEditing: boolean;
  isDeleting: boolean;
  onAdd: (data: LedgerPaymentCreateInput) => Promise<void>;
  onEdit: (paymentId: number, data: LedgerPaymentUpdateInput) => Promise<void>;
  onDelete: (paymentId: number) => Promise<void>;
};

export function EditablePaymentsCell({
  payments,
  checkTarget,
  remaining,
  isAdding,
  isEditing,
  isDeleting,
  onAdd,
  onEdit,
  onDelete,
}: EditablePaymentsCellProps) {
  return (
    <div className="space-y-1.5">
      {payments.length === 0 ? (
        <span className="text-muted-foreground">Sin pagos registrados</span>
      ) : (
        <ul className="space-y-1.5">
          {payments.map((payment) => (
            <li
              key={payment.id}
              className="flex items-center justify-between gap-2 whitespace-nowrap"
            >
              <Badge variant="outline">{getPaymentMethodLabel(payment.method)}</Badge>
              <span className="font-medium">{formatCurrency(payment.amount)}</span>
              <span className="text-muted-foreground text-[11px]">
                {formatDateTime(payment.date)}
              </span>
              <div className="flex items-center gap-0.5">
                <PaymentFormDialog
                  title="Editar pago"
                  remaining={remaining + Number(payment.amount)}
                  isPending={isEditing}
                  initialValues={{
                    amount: Number(payment.amount),
                    method: payment.method,
                    date: payment.date,
                  }}
                  onSubmit={(data) => onEdit(payment.id, data)}
                  trigger={
                    <Button
                      type="button"
                      variant="ghost"
                      size="icon"
                      className="h-6 w-6 text-muted-foreground hover:text-foreground"
                    >
                      <Pencil className="h-3.5 w-3.5" />
                    </Button>
                  }
                />
                <DeletePaymentButton
                  isPending={isDeleting}
                  onConfirm={() => onDelete(payment.id)}
                />
              </div>
            </li>
          ))}
        </ul>
      )}

      {remaining > 0 && (
        <PaymentFormDialog
          title="Agregar pago"
          remaining={remaining}
          isPending={isAdding}
          checkTarget={checkTarget}
          onSubmit={(data) => onAdd(data as LedgerPaymentCreateInput)}
          trigger={
            <Button type="button" variant="outline" size="sm" className="h-6 px-2 text-xs">
              <Plus className="mr-1 h-3 w-3" />
              Agregar pago
            </Button>
          }
        />
      )}

      {/* Cheques cargados que todavía no se acreditaron (no mueven el saldo) */}
      {checkTarget && (
        <DocumentPendingChecksBadge
          documentType={
            checkTarget.direction === "received" ? checkTarget.documentType : "purchase_invoice"
          }
          documentId={checkTarget.documentId}
        />
      )}
    </div>
  );
}