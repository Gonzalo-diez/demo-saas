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
  SalesTypeBadge,
} from "@/features/admin/account-ledger/components/ledger-helpers";
import {
  useAddClientPayment,
  useDeleteClientPayment,
  useEditClientPayment,
} from "@/features/admin/account-ledger/hooks/use-client-payment-mutations";
import type { ClientSaleRow } from "@/features/admin/account-ledger/types";

export function ClientSalesTable({ rows }: { rows: ClientSaleRow[] }) {
  const addPayment = useAddClientPayment();
  const editPayment = useEditClientPayment();
  const deletePayment = useDeleteClientPayment();

  if (rows.length === 0) {
    return (
      <p className="py-8 text-center text-sm text-muted-foreground">
        No hay ventas a clientes cargadas para este filtro.
      </p>
    );
  }

  function paymentsCellFor(row: ClientSaleRow) {
    return (
      <EditablePaymentsCell
        payments={row.payments}
        checkTarget={
          row.client_id != null
            ? {
                direction: "received",
                client: { id: row.client_id, name: row.client_name },
                documentType: row.document_type,
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
              salesInvoiceId: row.id,
              documentType: row.document_type,
              data,
            })
            .then(() => {})
        }
        onEdit={(paymentId, data) =>
          editPayment.mutateAsync({ allocationId: paymentId, data }).then(() => {})
        }
        onDelete={(paymentId) => deletePayment.mutateAsync(paymentId).then(() => {})}
      />
    );
  }

  return (
    <div className="space-y-4">
      {/* Vista mobile: cards */}
      <div className="space-y-3 md:hidden">
        {rows.map((row) => (
          <div key={`${row.document_type}-${row.id}`} className="space-y-3 rounded-2xl border bg-background p-4 shadow-sm">
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0 space-y-1">
                <p className="truncate font-semibold">{row.client_name}</p>
                <div className="flex items-center gap-2">
                  <p className="text-xs text-muted-foreground">
                    {formatDateOnly(row.sale_date)}
                  </p>
                  <SalesTypeBadge salesType={row.sales_type ?? "B2B"} />
                </div>
              </div>
              <div className="flex flex-col items-end gap-1">
                <DocumentTypeBadge
                  documentType={row.document_type}
                  documentNumber={row.document_number}
                />
                <LedgerPaymentStatusBadge status={row.payment_status} />
              </div>
            </div>

            <div className="rounded-xl border p-3 text-sm">
              <p className="mb-1 text-xs text-muted-foreground">
                Producto/s (cant. / stock restante)
              </p>
              <ProductLinesCell products={row.products} showStock />
            </div>

            <div className="grid grid-cols-3 gap-3 text-sm">
              <div className="rounded-xl border p-3">
                <p className="text-xs text-muted-foreground">Cant. total</p>
                <p className="font-medium">{row.total_quantity}</p>
              </div>
              <div className="rounded-xl border p-3">
                <p className="text-xs text-muted-foreground">Total</p>
                <p className="font-medium">{formatCurrency(row.total_amount)}</p>
              </div>
              <div className="rounded-xl border p-3">
                <p className="text-xs text-muted-foreground">Deuda</p>
                <p className="font-medium">{formatCurrency(row.balance)}</p>
              </div>
            </div>

            <div className="rounded-xl border p-3 text-sm">
              <p className="mb-1 text-xs text-muted-foreground">Formas de pago</p>
              {paymentsCellFor(row)}
            </div>
          </div>
        ))}
      </div>

      {/* Vista desktop: tabla */}
      <div className="hidden overflow-x-auto rounded-2xl border bg-background shadow-sm md:block">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Fecha</TableHead>
              <TableHead>Cliente</TableHead>
              <TableHead>Documento</TableHead>
              <TableHead>Tipo</TableHead>
              <TableHead>Producto/s (cant. / stock restante)</TableHead>
              <TableHead className="text-right">Cant. total</TableHead>
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
                  {formatDateOnly(row.sale_date)}
                </TableCell>
                <TableCell className="align-top font-medium">{row.client_name}</TableCell>
                <TableCell className="align-top">
                  <DocumentTypeBadge
                    documentType={row.document_type}
                    documentNumber={row.document_number}
                  />
                </TableCell>
                <TableCell className="align-top">
                  <SalesTypeBadge salesType={row.sales_type ?? "B2B"} />
                </TableCell>
                <TableCell className="align-top">
                  <ProductLinesCell products={row.products} showStock />
                </TableCell>
                <TableCell className="text-right align-top">{row.total_quantity}</TableCell>
                <TableCell className="align-top">{paymentsCellFor(row)}</TableCell>
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
      </div>
    </div>
  );
}