from __future__ import annotations

from sqlalchemy import literal, select
from sqlalchemy.sql.selectable import Subquery

from app.models.sales_invoice_item_model import SalesInvoiceItem
from app.models.sales_invoice_model import SalesInvoice
from app.models.sales_quote_item_model import SalesQuoteItem
from app.models.sales_quote_model import SalesQuote

"""
Fuente única de "ventas reales" para todo analytics.

Desde que un pedido (Order) puede convertirse en un remito (SalesInvoice) o
en un presupuesto (SalesQuote con order_id) según lo haya elegido el cliente
en la tienda online o el vendedor en una venta B2B, cualquier métrica de
ventas que solo mire SalesInvoice deja afuera la mitad de las ventas.

Estas dos funciones devuelven una UNION ALL de ambas tablas con las mismas
columnas, para que cada servicio de analytics arme su query una sola vez
contra "la venta", sin importar qué documento la generó. Los presupuestos
sueltos (order_id NULL: cotizaciones que no nacieron de un pedido) quedan
afuera a propósito: no son ventas, todavía no hay nada vendido.

Las columnas devueltas imitan a SalesInvoice / SalesInvoiceItem
(invoice_date -> doc_date, sales_invoice_id -> sales_document_id) para que
el resto del código cambie lo mínimo posible.
"""


def sales_documents_subquery(*, confirmed_only: bool) -> Subquery:
    """
    Cabecera: id, source, doc_date, status, client_id, client_branch_id,
    sales_rep_id, total_amount, total_cost, margin_amount.

    confirmed_only=True  -> solo remitos 'confirmed' / presupuestos 'approved'
                             (el documento quedó cerrado, no un borrador).
    confirmed_only=False -> cualquier estado salvo 'cancelled'.

    El `id` NO es único entre remitos y presupuestos (ambas tablas arrancan
    en 1): para unir con los ítems hay que filtrar siempre también por
    `source`, tal como hace sales_document_items_subquery.
    """
    invoices = select(
        SalesInvoice.id.label("id"),
        literal("sales_invoice").label("source"),
        SalesInvoice.invoice_date.label("doc_date"),
        SalesInvoice.status.label("status"),
        SalesInvoice.client_id.label("client_id"),
        SalesInvoice.client_branch_id.label("client_branch_id"),
        SalesInvoice.sales_rep_id.label("sales_rep_id"),
        SalesInvoice.total_amount.label("total_amount"),
        SalesInvoice.total_cost.label("total_cost"),
        SalesInvoice.margin_amount.label("margin_amount"),
    )
    invoices = invoices.where(
        SalesInvoice.status == "confirmed"
        if confirmed_only
        else SalesInvoice.status != "cancelled"
    )

    quotes = (
        select(
            SalesQuote.id.label("id"),
            literal("sales_quote").label("source"),
            SalesQuote.quote_date.label("doc_date"),
            SalesQuote.status.label("status"),
            SalesQuote.client_id.label("client_id"),
            SalesQuote.client_branch_id.label("client_branch_id"),
            SalesQuote.sales_rep_id.label("sales_rep_id"),
            SalesQuote.total_amount.label("total_amount"),
            SalesQuote.total_cost.label("total_cost"),
            SalesQuote.margin_amount.label("margin_amount"),
        )
        .where(SalesQuote.order_id.is_not(None))
    )
    quotes = quotes.where(
        SalesQuote.status == "approved"
        if confirmed_only
        else SalesQuote.status != "cancelled"
    )

    return invoices.union_all(quotes).subquery("sales_documents")


def sales_document_items_subquery(*, confirmed_only: bool) -> Subquery:
    """
    Ítems: sales_document_id, source, product_id, quantity, subtotal,
    subtotal_cost, margin_amount, doc_date, status, client_id,
    client_branch_id, sales_rep_id.

    La cabecera va denormalizada en cada fila (doc_date, client_id, etc.)
    para que cada servicio pueda filtrar/agrupar directo sobre los ítems,
    sin otro join.
    """
    invoice_items = (
        select(
            SalesInvoiceItem.sales_invoice_id.label("sales_document_id"),
            literal("sales_invoice").label("source"),
            SalesInvoiceItem.product_id.label("product_id"),
            SalesInvoiceItem.quantity.label("quantity"),
            SalesInvoiceItem.subtotal.label("subtotal"),
            SalesInvoiceItem.subtotal_cost.label("subtotal_cost"),
            SalesInvoiceItem.margin_amount.label("margin_amount"),
            SalesInvoice.invoice_date.label("doc_date"),
            SalesInvoice.status.label("status"),
            SalesInvoice.client_id.label("client_id"),
            SalesInvoice.client_branch_id.label("client_branch_id"),
            SalesInvoice.sales_rep_id.label("sales_rep_id"),
        )
        .join(SalesInvoice, SalesInvoice.id == SalesInvoiceItem.sales_invoice_id)
    )
    invoice_items = invoice_items.where(
        SalesInvoice.status == "confirmed"
        if confirmed_only
        else SalesInvoice.status != "cancelled"
    )

    quote_items = (
        select(
            SalesQuoteItem.sales_quote_id.label("sales_document_id"),
            literal("sales_quote").label("source"),
            SalesQuoteItem.product_id.label("product_id"),
            SalesQuoteItem.quantity.label("quantity"),
            SalesQuoteItem.subtotal.label("subtotal"),
            SalesQuoteItem.subtotal_cost.label("subtotal_cost"),
            SalesQuoteItem.margin_amount.label("margin_amount"),
            SalesQuote.quote_date.label("doc_date"),
            SalesQuote.status.label("status"),
            SalesQuote.client_id.label("client_id"),
            SalesQuote.client_branch_id.label("client_branch_id"),
            SalesQuote.sales_rep_id.label("sales_rep_id"),
        )
        .join(SalesQuote, SalesQuote.id == SalesQuoteItem.sales_quote_id)
        .where(SalesQuote.order_id.is_not(None))
    )
    quote_items = quote_items.where(
        SalesQuote.status == "approved"
        if confirmed_only
        else SalesQuote.status != "cancelled"
    )

    return invoice_items.union_all(quote_items).subquery("sales_document_items")