/**
 * Documento de la fila de Cuenta corriente sobre el que se puede pagar con cheque:
 *  - received: cheque de un cliente para un remito/presupuesto de venta.
 *  - issued: cheque propio a un proveedor, solo para remitos de compra
 *    (los presupuestos de compra nunca admiten pagos).
 */
export type LedgerCheckTarget =
  | {
      direction: "received";
      client: { id: number; name: string };
      documentType: "sales_invoice" | "sales_quote";
      documentId: number;
      documentNumber: string;
    }
  | {
      direction: "issued";
      supplier: { id: number; name: string };
      documentId: number;
      documentNumber: string;
    };
