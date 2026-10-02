from __future__ import annotations
from decimal import Decimal
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from app.models.sales_invoice_model import SalesInvoice

def _money(value: Decimal | int | float | None) -> str:
    """Format a number as Argentine money string (e.g. 1.275,00)."""
    value = value or Decimal("0")
    return (
        f"{Decimal(value):,.2f}"
        .replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )


def build_sales_invoice_pdf(invoice: SalesInvoice) -> bytes:
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    ML = 50          # margin left
    MR = width - 50  # margin right

    # Column x positions (matching example layout)
    col_qty      = ML
    col_product  = ML + 50
    col_price    = MR - 200
    col_disc     = MR - 100
    col_subtotal = MR

    pdf.setTitle(f"remito-venta-{invoice.invoice_number}.pdf")

    y = height - 50

    # ── HEADER ────────────────────────────────────────────
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(ML, y, "REMITO")
    y -= 24

    # ── DATE ──────────────────────────────────────────────
    pdf.setFont("Helvetica", 10)
    pdf.drawString(ML, y, invoice.invoice_date.strftime("%d/%m/%Y"))
    y -= 22

    # ── CUSTOMER BLOCK ────────────────────────────────────
    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawString(ML, y, (invoice.customer_name or "").upper())
    y -= 16

    pdf.setFont("Helvetica", 10)
    pdf.drawString(ML, y, "CONSUMIDOR FINAL")
    y -= 16

    # Payment / seller info (sales_type and notes as a one-liner)
    meta_parts = []
    if invoice.sales_type:
        meta_parts.append(invoice.sales_type.value.upper())
    if invoice.notes:
        meta_parts.append(invoice.notes.upper())
    if meta_parts:
        pdf.drawString(ML, y, "  ".join(meta_parts))
        y -= 16

    y -= 10

    # ── ITEMS TABLE ───────────────────────────────────────
    pdf.setFont("Helvetica", 10)

    for item in invoice.items:
        # Page break if needed
        if y < 100:
            pdf.showPage()
            y = height - 50
            pdf.setFont("Helvetica", 10)

        qty_str  = str(item.quantity)
        name_str = item.product_name
        if item.product_brand:
            name_str += f" - {item.product_brand}"

        price_str    = _money(item.unit_price)
        disc_str     = "0,00"
        subtotal_str = _money(item.subtotal)

        pdf.drawString(col_qty,                     y, qty_str)
        pdf.drawString(col_product,                 y, name_str[:42])
        pdf.drawRightString(col_price,              y, price_str)
        pdf.drawRightString(col_disc,               y, disc_str)
        pdf.drawRightString(col_subtotal,           y, subtotal_str)

        y -= 18

    y -= 6

    # ── SEPARATOR ─────────────────────────────────────────
    pdf.setStrokeColor(colors.black)
    pdf.line(ML, y, MR, y)
    y -= 16

    # ── TOTAL ─────────────────────────────────────────────
    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawRightString(col_subtotal, y, f"$ {_money(invoice.total_amount)}")
    y -= 18

    # Secondary totals (cost / margin) if present
    pdf.setFont("Helvetica", 10)
    if invoice.total_cost is not None:
        pdf.drawRightString(col_subtotal, y, _money(invoice.total_cost))
        y -= 15

    if invoice.margin_amount is not None:
        pdf.drawRightString(col_subtotal, y, _money(invoice.margin_amount))
        y -= 15

    # Always show a trailing 0,00 line (like the examples)
    y -= 2
    pdf.drawRightString(col_subtotal, y, "0,00")

    pdf.showPage()
    pdf.save()

    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes