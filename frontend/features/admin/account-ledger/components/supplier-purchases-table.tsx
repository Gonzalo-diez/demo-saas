import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { EditablePaymentsCell } from "@/features/admin/account-ledger/components/editable-payments-cell";
import {
  DocumentTypeBadge,
  formatCurrency,
  formatDateOnly,
  LedgerPaymentStatusBadge,
  ProductLinesCell,
} from "@/features/admin/account-ledger/components/ledger-helpers";
import {
  useAddSupplierPayment,
  useDeleteSupplierPayment,
  useEditSupplierPayment,
} from "@/features/admin/account-ledger/hooks/use-supplier-payment-mutations";
import type { SupplierPurchaseRow } from "@/features/admin/account-ledger/types";

export function SupplierPurchasesTable({ rows }: { rows: SupplierPurchaseRow[] }) {
  const addPayment = useAddSupplierPayment();
  const editPayment = useEditSupplierPayment();
  const deletePayment = useDeleteSupplierPayment();

  if (rows.length === 0) {
    return (
      <p className="py-8 text-center text-sm text-muted-foreground">
        Este vendedor todavía no tiene compras a proveedores cargadas.
      </p>
    );
  }

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Fecha</TableHead>
          <TableHead>Proveedor</TableHead>
          <TableHead>Documento</TableHead>
          <TableHead>Producto/s</TableHead>
          <TableHead className="text-right">Cantidad</TableHead>
          <TableHead>Formas de pago</TableHead>
          <TableHead className="text-right">Total</TableHead>
          <TableHead className="text-right">Deuda</TableHead>
          <TableHead>Estado</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {rows.map((row) => (
          <TableRow key={`${row.document_type}-${row.id}`}>
            <TableCell className="whitespace-nowrap align-top">
              {formatDateOnly(row.purchase_date)}
            </TableCell>
            <TableCell className="align-top font-medium">{row.supplier_name}</TableCell>
            <TableCell className="align-top">
              <DocumentTypeBadge
                documentType={row.document_type}
                documentNumber={row.document_number}
              />
            </TableCell>
            <TableCell className="align-top">
              <ProductLinesCell products={row.products} />
            </TableCell>
            <TableCell className="text-right align-top">{row.total_quantity}</TableCell>
            <TableCell className="align-top">
              <EditablePaymentsCell
                payments={row.payments}
                checkTarget={
                  row.supplier_id != null && row.document_type === "purchase_invoice"
                    ? {
                        direction: "issued",
                        supplier: { id: row.supplier_id, name: row.supplier_name },
                        documentId: row.id,
                        documentNumber: row.document_number,
                      }
                    : undefined
                }
                remaining={Number(row.balance)}
                isAdding={addPayment.isPending}
                isEditing={editPayment.isPending}
                isDeleting={deletePayment.isPending}
                onAdd={(data) =>
                  addPayment
                    .mutateAsync({
                      purchaseInvoiceId: row.id,
                      documentType: row.document_type,
                      data,
                    })
                    .then(() => {})
                }
                onEdit={(paymentId, data) =>
                  editPayment.mutateAsync({ allocationId: paymentId, data }).then(() => {})
                }
                onDelete={(paymentId) =>
                  deletePayment.mutateAsync(paymentId).then(() => {})
                }
              />
            </TableCell>
            <TableCell className="text-right align-top whitespace-nowrap">
              {formatCurrency(row.total_amount)}
            </TableCell>
            <TableCell className="text-right align-top whitespace-nowrap">
              {formatCurrency(row.balance)}
            </TableCell>
            <TableCell className="align-top">
              <LedgerPaymentStatusBadge status={row.payment_status} />
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}