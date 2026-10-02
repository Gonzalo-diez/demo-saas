from __future__ import annotations

from decimal import Decimal
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from app.models.purchase_invoice_model import PurchaseInvoice


def _money(value: Decimal | int | float | None) -> str:
    """Format a number as Argentine money string (e.g. 1.275,00)."""
    value = value or Decimal("0")
    return (
        f"{Decimal(value):,.2f}"
        .replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )


def build_purchase_invoice_pdf(invoice: PurchaseInvoice) -> bytes:
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    ML = 50          # margin left
    MR = width - 50  # margin right

    # Column x positions
    col_qty      = ML
    col_product  = ML + 50
    col_sku      = ML + 260
    col_price    = MR - 100
    col_subtotal = MR

    pdf.setTitle(f"remito-compra-{invoice.invoice_number}.pdf")

    y = height - 50

    # ── DATE ──────────────────────────────────────────────
    pdf.setFont("Helvetica", 10)
    pdf.drawString(ML, y, invoice.invoice_date.strftime("%d/%m/%Y"))
    y -= 22

    # ── SUPPLIER BLOCK ────────────────────────────────────
    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawString(ML, y, (invoice.supplier_name or "").upper())
    y -= 16

    pdf.setFont("Helvetica", 10)
    if invoice.supplier_tax_id:
        pdf.drawString(ML, y, f"CUIT: {invoice.supplier_tax_id}")
        y -= 16

    # Invoice number
    pdf.drawString(ML, y, f"Remito N°: {invoice.invoice_number}")
    y -= 16

    if invoice.notes:
        pdf.drawString(ML, y, invoice.notes.upper())
        y -= 16

    y -= 10

    # ── COLUMN HEADERS ────────────────────────────────────
    pdf.setFont("Helvetica-Bold", 9)
    pdf.drawString(col_qty,      y, "CANT.")
    pdf.drawString(col_product,  y, "PRODUCTO")
    pdf.drawString(col_sku,      y, "SKU")
    pdf.drawRightString(col_price,    y, "P. UNITARIO")
    pdf.drawRightString(col_subtotal, y, "SUBTOTAL")
    y -= 4
    pdf.setStrokeColor(colors.black)
    pdf.line(ML, y, MR, y)
    y -= 14

    # ── ITEMS TABLE ───────────────────────────────────────
    pdf.setFont("Helvetica", 10)

    for item in invoice.items:
        # Page break if needed
        if y < 100:
            pdf.showPage()
            y = height - 50
            pdf.setFont("Helvetica", 10)

        qty_str      = str(item.quantity)
        name_str     = item.product_name[:35]
        sku_str      = item.product_sku or ""
        price_str    = _money(item.unit_cost)
        subtotal_str = _money(item.subtotal)

        pdf.drawString(col_qty,                   y, qty_str)
        pdf.drawString(col_product,               y, name_str)
        pdf.drawString(col_sku,                   y, sku_str[:18])
        pdf.drawRightString(col_price,            y, price_str)
        pdf.drawRightString(col_subtotal,         y, subtotal_str)

        y -= 18

    y -= 6

    # ── SEPARATOR ─────────────────────────────────────────
    pdf.setStrokeColor(colors.black)
    pdf.line(ML, y, MR, y)
    y -= 16

    # ── TOTAL ─────────────────────────────────────────────
    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawRightString(col_subtotal, y, f"$ {_money(invoice.total_amount)}")

    pdf.showPage()
    pdf.save()

    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
