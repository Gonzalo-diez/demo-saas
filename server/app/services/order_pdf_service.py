from __future__ import annotations
from io import BytesIO
from decimal import Decimal
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas
from app.models.order_model import Order

def _money(value: Decimal | int | float, currency: str) -> str:
    return f"{currency} {Decimal(value):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def build_order_pdf(order: Order) -> bytes:
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    left = 40
    right = width - 40
    y = height - 40

    def draw_line(text: str, *, size: int = 10, bold: bool = False, gap: int = 16):
        nonlocal y
        font_name = "Helvetica-Bold" if bold else "Helvetica"
        pdf.setFont(font_name, size)
        pdf.drawString(left, y, text)
        y -= gap

    def draw_wrapped(label: str, value: str | None, *, size: int = 10, gap: int = 14):
        nonlocal y
        text = f"{label}: {value or '-'}"
        pdf.setFont("Helvetica", size)

        max_width = right - left
        words = text.split()
        current = ""

        for word in words:
            tentative = f"{current} {word}".strip()
            if stringWidth(tentative, "Helvetica", size) <= max_width:
                current = tentative
            else:
                pdf.drawString(left, y, current)
                y -= gap
                current = word

        if current:
            pdf.drawString(left, y, current)
            y -= gap

    def ensure_space(min_y: int = 80):
        nonlocal y
        if y < min_y:
            pdf.showPage()
            y = height - 40

    pdf.setTitle(f"pedido-{order.id}.pdf")

    draw_line("Resumen de pedido", size=16, bold=True, gap=22)
    draw_line(f"Pedido #{order.id}", size=12, bold=True)
    draw_line(f"Fecha: {order.created_at.strftime('%d/%m/%Y %H:%M')}", size=10)
    y -= 6

    draw_line("Datos del cliente", size=12, bold=True, gap=18)
    draw_wrapped("Nombre", order.customer_name)
    draw_wrapped("Teléfono", order.customer_phone)
    draw_wrapped("Email", order.customer_email)

    y -= 4
    draw_line("Entrega", size=12, bold=True, gap=18)
    draw_wrapped("Tipo", "Envío" if order.delivery_type == "delivery" else "Retiro")
    draw_wrapped("Dirección", order.delivery_address)
    draw_wrapped("Ciudad", order.delivery_city)
    draw_wrapped("Referencia", order.delivery_reference)

    y -= 4
    draw_line("Items", size=12, bold=True, gap=18)

    for item in order.items:
        ensure_space()
        draw_wrapped(
            "Producto",
            f"{item.product_name_snapshot} | Cant: {item.quantity} | Unitario: {_money(item.unit_price, order.currency)} | Subtotal: {_money(item.subtotal, order.currency)}",
        )

    y -= 4
    draw_line("Totales", size=12, bold=True, gap=18)
    draw_line(f"Total: {_money(order.total_amount, order.currency)}", size=11, bold=True)

    y -= 10
    draw_line(f"Estado actual: {order.status}", size=10)

    pdf.showPage()
    pdf.save()

    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes