from typing import Literal

from fastapi import HTTPException, status

SalesDocumentType = Literal["sales_invoice", "sales_quote"]


def ensure_sales_document_accepts_payments(
    document_type: SalesDocumentType,
    document,
    label: str,
) -> None:
    """
    Regla única de "¿este documento de venta se puede cobrar?", compartida por
    los dos caminos que registran cobros de clientes:

      - ClientAccountMovementService (cobros con imputaciones)
      - AccountLedgerService (cobros desde la pantalla de ventas a clientes)

    Un cobro solo tiene sentido si el documento generó deuda en la cuenta
    corriente del cliente. Si no la generó, el cobro dejaría un saldo a favor
    sin deuda previa.

      - Remito de venta: solo si está 'confirmed' (el borrador aún no registró
        deuda y el cancelado ya la revirtió).
      - Presupuesto de venta: solo si nació de un pedido (order_id) y está
        'approved'. Las cotizaciones sueltas no generan deuda.
    """
    if document_type == "sales_quote":
        if document.order_id is None or document.status != "approved":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"El {label} no admite cobros "
                    "(solo los presupuestos vigentes generados por un pedido)"
                ),
            )
        return

    if document.status != "confirmed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"El {label} no admite cobros "
                "(solo los remitos confirmados)"
            ),
        )


def ensure_purchase_document_accepts_payments(
    document_type: Literal["purchase_invoice", "purchase_quote"],
    label: str,
) -> None:
    """
    Análogo de ensure_sales_document_accepts_payments, del lado compras.

    A diferencia de un presupuesto de venta (que sí genera deuda cuando nace
    de un pedido), un presupuesto de compra NUNCA genera deuda: no hay
    "pedido a proveedor" que lo convierta en remito, y PurchaseQuoteService
    lo deja explícitamente sin efecto en stock ni en cuenta corriente. Pagar
    contra un presupuesto de compra dejaría un saldo a favor del proveedor
    sin deuda real detrás, así que nunca se acepta un cobro sobre uno,
    venga de donde venga (carga manual o import).
    """
    if document_type == "purchase_quote":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"El {label} no admite pagos "
                "(un presupuesto de compra no genera deuda; "
                "el pago se registra sobre el remito de compra)"
            ),
        )