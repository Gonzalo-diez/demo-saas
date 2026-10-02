from __future__ import annotations

from decimal import Decimal
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from app.models.sales_quote_model import SalesQuote


def _money(value: Decimal | int | float | None) -> str:
    """Format a number as Argentine money string (e.g. 1.275,00)."""
    value = value or Decimal("0")
    return (
        f"{Decimal(value):,.2f}"
        .replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )


def build_sales_quote_pdf(quote: SalesQuote) -> bytes:
    """
    Genera el PDF del presupuesto de venta con el formato de referencia:
    fecha, cliente (o "CONSUMIDOR FINAL"), forma de pago, y una tabla con
    cantidad / producto / precio unitario / descuento (0,00) / total.
    """
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    ML = 50
    MR = width - 50

    col_qty      = ML
    col_product  = ML + 50
    col_price    = MR - 220
    col_discount = MR - 110
    col_subtotal = MR

    pdf.setTitle(f"presupuesto-venta-{quote.quote_number}.pdf")

    y = height - 50

    pdf.setFont("Helvetica-Bold", 13)
    pdf.drawString(ML, y, "PRESUPUESTO DE VENTA")
    y -= 22

    pdf.setFont("Helvetica", 10)
    pdf.drawString(ML, y, quote.quote_date.strftime("%d/%m/%Y"))
    y -= 22

    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawString(ML, y, (quote.customer_name or "CONSUMIDOR FINAL").upper())
    y -= 16

    pdf.setFont("Helvetica", 10)
    if quote.customer_tax_id:
        pdf.drawString(ML, y, f"CUIT/DNI: {quote.customer_tax_id}")
        y -= 16

    if quote.payment_method:
        pdf.drawString(ML, y, quote.payment_method.upper())
        y -= 16

    pdf.drawString(ML, y, f"Presupuesto N°: {quote.quote_number}")
    y -= 16

    if quote.valid_until:
        pdf.drawString(ML, y, f"Válido hasta: {quote.valid_until.strftime('%d/%m/%Y')}")
        y -= 16

    if quote.notes:
        pdf.drawString(ML, y, quote.notes.upper())
        y -= 16

    y -= 10

    pdf.setFont("Helvetica-Bold", 9)
    pdf.drawString(col_qty,      y, "CANT.")
    pdf.drawString(col_product,  y, "PRODUCTO")
    pdf.drawRightString(col_price,    y, "P. UNITARIO")
    pdf.drawRightString(col_discount, y, "DESC.")
    pdf.drawRightString(col_subtotal, y, "TOTAL")
    y -= 4
    pdf.setStrokeColor(colors.black)
    pdf.line(ML, y, MR, y)
    y -= 14

    pdf.setFont("Helvetica", 10)

    for item in quote.items:
        if y < 100:
            pdf.showPage()
            y = height - 50
            pdf.setFont("Helvetica", 10)

        pdf.drawString(col_qty,           y, str(item.quantity))
        pdf.drawString(col_product,       y, item.product_name[:40])
        pdf.drawRightString(col_price,    y, _money(item.unit_price))
        pdf.drawRightString(col_subtotal, y, _money(item.subtotal))

        y -= 18

    y -= 6

    pdf.setStrokeColor(colors.black)
    pdf.line(ML, y, MR, y)
    y -= 16

    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawRightString(col_subtotal, y, f"$ {_money(quote.total_amount)}")

    pdf.showPage()
    pdf.save()

    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes