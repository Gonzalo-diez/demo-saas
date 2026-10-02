from __future__ import annotations
import base64
import json
from urllib import error, request
from app.core.config import get_settings
from app.models.order_model import Order
from app.services.order_pdf_service import build_order_pdf
from app.services.sales_invoice_pdf_service import build_sales_invoice_pdf
from app.services.sales_quote_pdf_service import build_sales_quote_pdf
from app.models.sales_invoice_model import SalesInvoice
from app.models.sales_quote_model import SalesQuote

settings = get_settings()

def _is_email_enabled() -> bool:
    return bool(
        settings.RESEND_API_KEY
        and settings.ORDER_FROM_EMAIL
        and settings.ORDER_ADMIN_EMAIL
    )

def _post_email_payload(payload: dict) -> None:
    if not settings.RESEND_API_KEY:
        raise RuntimeError("RESEND_API_KEY no está configurada.")

    req = request.Request(
        url="https://api.resend.com/emails",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {settings.RESEND_API_KEY}",
            "Content-Type": "application/json",
            "User-Agent": "distribuidora-backend/1.0",
        },
        method="POST",
    )

    try:
        with request.urlopen(req, timeout=20) as response:
            status_code = response.getcode()
            body = response.read().decode("utf-8")
            if status_code >= 300:
                raise RuntimeError(f"Resend respondió {status_code}: {body}")

    except error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"Error HTTP de Resend {exc.code}: {body}") from exc
    except error.URLError as exc:
        raise RuntimeError(f"No se pudo conectar con Resend: {exc.reason}") from exc

def _build_attachment(order: Order) -> dict:
    pdf_bytes = build_order_pdf(order)
    return {
        "filename": f"pedido-{order.id}.pdf",
        "content": base64.b64encode(pdf_bytes).decode("utf-8"),
    }
    
def _build_invoice_attachment(invoice: SalesInvoice) -> dict:
    pdf_bytes = build_sales_invoice_pdf(invoice)
    return {
        "filename": f"remito-{invoice.invoice_number}.pdf",
        "content": base64.b64encode(pdf_bytes).decode("utf-8"),
    }

def _build_sales_quote_attachment(quote: SalesQuote) -> dict:
    pdf_bytes = build_sales_quote_pdf(quote)
    return {
        "filename": f"presupuesto-{quote.quote_number}.pdf",
        "content": base64.b64encode(pdf_bytes).decode("utf-8"),
    }


def _format_currency(amount, currency: str = "ARS") -> str:
    try:
        return f"{currency} {float(amount):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except (TypeError, ValueError):
        return f"{currency} -"

def _build_items_html(order: Order) -> str:
    """
    Genera la tabla de ítems del pedido con imagen, nombre, cantidad y precio.
    Usa product_image_url_snapshot — imagen fija al momento de crear la orden.
    """
    if not order.items:
        return ""

    rows = ""
    for item in order.items:
        if item.product_image_url_snapshot:
            img_html = (
                f'<img src="{item.product_image_url_snapshot}" alt="{item.product_name_snapshot}" '
                f'width="56" height="56" '
                f'style="width:56px;height:56px;object-fit:cover;'
                f'border-radius:6px;display:block;border:1px solid #e5e7eb;">'
            )
        else:
            # Placeholder con inicial del producto
            inicial = (item.product_name_snapshot or "?")[0].upper()
            img_html = (
                f'<div style="width:56px;height:56px;border-radius:6px;'
                f'background:#f3f4f6;display:flex;align-items:center;'
                f'justify-content:center;font-size:20px;font-weight:600;'
                f'color:#9ca3af;border:1px solid #e5e7eb;">{inicial}</div>'
            )

        brand_line = (
            f'<span style="font-size:12px;color:#6b7280;">'
            f'{item.product_brand_snapshot}</span><br>'
            if item.product_brand_snapshot
            else ""
        )

        sku_line = (
            f'<span style="font-size:11px;color:#9ca3af;">'
            f'SKU: {item.product_sku_snapshot}</span>'
            if item.product_sku_snapshot
            else ""
        )

        rows += f"""
        <tr>
          <td style="padding:12px 8px;border-bottom:1px solid #f3f4f6;vertical-align:middle;width:72px;">
            {img_html}
          </td>
          <td style="padding:12px 8px;border-bottom:1px solid #f3f4f6;vertical-align:middle;">
            <span style="font-size:14px;font-weight:500;color:#111827;">
              {item.product_name_snapshot}
            </span><br>
            {brand_line}
            {sku_line}
          </td>
          <td style="padding:12px 8px;border-bottom:1px solid #f3f4f6;
                     vertical-align:middle;text-align:center;white-space:nowrap;">
            <span style="font-size:14px;color:#374151;">x{item.quantity}</span>
          </td>
          <td style="padding:12px 8px;border-bottom:1px solid #f3f4f6;
                     vertical-align:middle;text-align:right;white-space:nowrap;">
            <span style="font-size:14px;color:#374151;">
              {_format_currency(item.unit_price, order.currency)}
            </span><br>
            <span style="font-size:12px;color:#6b7280;">
              Subtotal: {_format_currency(item.subtotal, order.currency)}
            </span>
          </td>
        </tr>
        """

    return f"""
    <table style="width:100%;border-collapse:collapse;margin:16px 0;">
      <thead>
        <tr style="border-bottom:2px solid #e5e7eb;">
          <th style="padding:8px;text-align:left;font-size:12px;
                     color:#6b7280;font-weight:500;width:72px;">Foto</th>
          <th style="padding:8px;text-align:left;font-size:12px;
                     color:#6b7280;font-weight:500;">Producto</th>
          <th style="padding:8px;text-align:center;font-size:12px;
                     color:#6b7280;font-weight:500;">Cant.</th>
          <th style="padding:8px;text-align:right;font-size:12px;
                     color:#6b7280;font-weight:500;">Precio</th>
        </tr>
      </thead>
      <tbody>
        {rows}
      </tbody>
    </table>
    """

def _build_delivery_block(order: Order) -> str:
    if order.delivery_type == "delivery":
        date_line = (
            f'<p style="margin:4px 0;font-size:14px;color:#374151;">'
            f'<strong>Fecha preferida:</strong> {order.preferred_delivery_date}</p>'
            if order.preferred_delivery_date else ""
        )
        return f"""
        <div style="background:#f9fafb;border-radius:8px;padding:16px;margin:16px 0;">
          <p style="margin:0 0 8px;font-size:13px;font-weight:600;
                    color:#6b7280;text-transform:uppercase;letter-spacing:.05em;">
            Datos de envío
          </p>
          <p style="margin:4px 0;font-size:14px;color:#374151;">
            <strong>Dirección:</strong> {order.delivery_address}, {order.delivery_city}
          </p>
          {date_line}
        </div>
        """
    else:
        return """
        <div style="background:#f9fafb;border-radius:8px;padding:16px;margin:16px 0;">
          <p style="margin:0;font-size:14px;color:#374151;">
            <strong>Modalidad:</strong> Retiro en local
          </p>
        </div>
        """

def _base_email_wrapper(content: str) -> str:
    """Envuelve el contenido en un layout de email limpio y compatible."""
    return f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="margin:0;padding:0;background:#f3f4f6;font-family:-apple-system,
                 BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">
      <table width="100%" cellpadding="0" cellspacing="0"
             style="background:#f3f4f6;padding:32px 16px;">
        <tr>
          <td align="center">
            <table width="600" cellpadding="0" cellspacing="0"
                   style="max-width:600px;width:100%;background:#ffffff;
                          border-radius:12px;overflow:hidden;
                          box-shadow:0 1px 3px rgba(0,0,0,.1);">
              <tr>
                <td style="padding:32px 32px 24px;">
                  {content}
                </td>
              </tr>
              <tr>
                <td style="padding:16px 32px 24px;border-top:1px solid #f3f4f6;
                           text-align:center;">
                  <p style="margin:0;font-size:12px;color:#9ca3af;">
                    Este es un mensaje automático. Por favor no respondas este email.
                  </p>
                </td>
              </tr>
            </table>
          </td>
        </tr>
      </table>
    </body>
    </html>
    """

def send_order_customer_email(order: Order) -> None:
    if not _is_email_enabled():
        raise RuntimeError("Email no configurado. Faltan variables de entorno.")

    if not order.customer_email:
        return

    items_html = _build_items_html(order)
    delivery_html = _build_delivery_block(order)

    content = f"""
    <h2 style="margin:0 0 4px;font-size:22px;font-weight:600;color:#111827;">
      ¡Recibimos tu pedido!
    </h2>
    <p style="margin:0 0 24px;font-size:15px;color:#6b7280;">
      Hola <strong>{order.customer_name}</strong>, gracias por tu compra.
      En breve nos pondremos en contacto para confirmar tu pedido.
    </p>

    <div style="background:#f9fafb;border-radius:8px;padding:12px 16px;
                margin-bottom:16px;display:flex;justify-content:space-between;">
      <span style="font-size:13px;color:#6b7280;">Pedido</span>
      <span style="font-size:14px;font-weight:600;color:#111827;">#{order.id}</span>
    </div>

    {items_html}
    {delivery_html}

    <table style="width:100%;margin-top:8px;">
      <tr>
        <td style="font-size:15px;color:#374151;font-weight:500;">Total del pedido</td>
        <td style="font-size:18px;font-weight:700;color:#111827;text-align:right;">
          {_format_currency(order.total_amount, order.currency)}
        </td>
      </tr>
    </table>

    <p style="margin:24px 0 0;font-size:13px;color:#9ca3af;">
      También te adjuntamos el resumen en PDF.
    </p>
    """

    payload = {
        "from": settings.ORDER_FROM_EMAIL,
        "to": [order.customer_email],
        "subject": f"Pedido recibido — {order.customer_name}",
        "html": _base_email_wrapper(content),
        "attachments": [_build_attachment(order)],
    }

    _post_email_payload(payload)

def send_order_admin_email(order: Order) -> None:
    if not _is_email_enabled():
        raise RuntimeError("Email no configurado. Faltan variables de entorno.")

    items_html = _build_items_html(order)
    delivery_label = "Envío a domicilio" if order.delivery_type == "delivery" else "Retiro en local"
    customer_email_line = order.customer_email or "—"

    content = f"""
    <h2 style="margin:0 0 4px;font-size:22px;font-weight:600;color:#111827;">
      Nuevo pedido #{order.id}
    </h2>
    <p style="margin:0 0 24px;font-size:14px;color:#6b7280;">
      Recibiste un nuevo pedido desde la tienda online.
    </p>

    <div style="background:#f9fafb;border-radius:8px;padding:16px;margin-bottom:16px;">
      <p style="margin:0 0 8px;font-size:13px;font-weight:600;color:#6b7280;
                text-transform:uppercase;letter-spacing:.05em;">Cliente</p>
      <p style="margin:4px 0;font-size:14px;color:#374151;">
        <strong>Nombre:</strong> {order.customer_name}
      </p>
      <p style="margin:4px 0;font-size:14px;color:#374151;">
        <strong>Teléfono:</strong> {order.customer_phone or "—"}
      </p>
      <p style="margin:4px 0;font-size:14px;color:#374151;">
        <strong>Email:</strong> {customer_email_line}
      </p>
      <p style="margin:4px 0;font-size:14px;color:#374151;">
        <strong>Entrega:</strong> {delivery_label}
      </p>
    </div>

    {items_html}

    <table style="width:100%;margin-top:8px;">
      <tr>
        <td style="font-size:15px;color:#374151;font-weight:500;">Total del pedido</td>
        <td style="font-size:18px;font-weight:700;color:#111827;text-align:right;">
          {_format_currency(order.total_amount, order.currency)}
        </td>
      </tr>
    </table>
    """

    payload = {
        "from": settings.ORDER_FROM_EMAIL,
        "to": [settings.ORDER_ADMIN_EMAIL],
        "subject": f"Nuevo pedido #{order.id} — {order.customer_name}",
        "html": _base_email_wrapper(content),
        "attachments": [_build_attachment(order)],
    }

    _post_email_payload(payload)

def send_order_shipped_email(order: Order) -> None:
    if not _is_email_enabled():
        raise RuntimeError("Email no configurado. Faltan variables de entorno.")

    if not order.customer_email:
        return

    items_html = _build_items_html(order)

    content = f"""
    <h2 style="margin:0 0 4px;font-size:22px;font-weight:600;color:#111827;">
      Tu pedido está en camino 🚚
    </h2>
    <p style="margin:0 0 24px;font-size:15px;color:#6b7280;">
      Hola <strong>{order.customer_name}</strong>, tu pedido fue despachado y está en camino.
    </p>

    {items_html}

    <table style="width:100%;margin-top:8px;">
      <tr>
        <td style="font-size:15px;color:#374151;font-weight:500;">Total</td>
        <td style="font-size:18px;font-weight:700;color:#111827;text-align:right;">
          {_format_currency(order.total_amount, order.currency)}
        </td>
      </tr>
    </table>
    """

    payload = {
        "from": settings.ORDER_FROM_EMAIL,
        "to": [order.customer_email],
        "subject": f"Tu pedido está en camino",
        "html": _base_email_wrapper(content),
    }

    _post_email_payload(payload)

def send_order_delivered_email(order: Order) -> None:
    if not _is_email_enabled():
        raise RuntimeError("Email no configurado. Faltan variables de entorno.")

    if not order.customer_email:
        return

    content = f"""
    <h2 style="margin:0 0 4px;font-size:22px;font-weight:600;color:#111827;">
      Pedido entregado ✓
    </h2>
    <p style="margin:0 0 24px;font-size:15px;color:#6b7280;">
      Hola <strong>{order.customer_name}</strong>, tu pedido fue entregado exitosamente. ¡Gracias por tu compra!
    </p>

    <table style="width:100%;margin-top:8px;">
      <tr>
        <td style="font-size:15px;color:#374151;font-weight:500;">Total</td>
        <td style="font-size:18px;font-weight:700;color:#111827;text-align:right;">
          {_format_currency(order.total_amount, order.currency)}
        </td>
      </tr>
    </table>
    """

    payload = {
        "from": settings.ORDER_FROM_EMAIL,
        "to": [order.customer_email],
        "subject": f"Tu pedido fue entregado",
        "html": _base_email_wrapper(content),
    }

    _post_email_payload(payload)
    
def send_invoice_customer_email(
    order: Order,
    invoice: SalesInvoice,
) -> None:
    """
    Envía el remito de venta al cliente cuando la orden pasa a 'preparing'.
    Solo se envía si hay email del cliente.
    """
    if not _is_email_enabled():
        raise RuntimeError("Email no configurado. Faltan variables de entorno.")

    recipient = order.customer_email
    if not recipient:
        return

    items_html = _build_items_html(order)

    content = f"""
    <h2 style="margin:0 0 4px;font-size:22px;font-weight:600;color:#111827;">
      Tu remito está listo
    </h2>
    <p style="margin:0 0 24px;font-size:15px;color:#6b7280;">
      Hola <strong>{order.customer_name}</strong>, adjuntamos el remito
      correspondiente a tu pedido.
    </p>

    <div style="background:#f9fafb;border-radius:8px;padding:12px 16px;
                margin-bottom:16px;">
      <table style="width:100%;">
        <tr>
          <td style="font-size:13px;color:#6b7280;">N° Remito</td>
          <td style="font-size:14px;font-weight:600;color:#111827;
                     text-align:right;">{invoice.invoice_number}</td>
        </tr>
        <tr>
          <td style="font-size:13px;color:#6b7280;padding-top:4px;">Fecha</td>
          <td style="font-size:14px;color:#374151;text-align:right;
                     padding-top:4px;">{invoice.invoice_date}</td>
        </tr>
      </table>
    </div>

    {items_html}

    <table style="width:100%;margin-top:8px;">
      <tr>
        <td style="font-size:15px;color:#374151;font-weight:500;">Total</td>
        <td style="font-size:18px;font-weight:700;color:#111827;text-align:right;">
          {_format_currency(invoice.total_amount, invoice.currency)}
        </td>
      </tr>
    </table>

    <p style="margin:24px 0 0;font-size:13px;color:#9ca3af;">
      Encontrás el remito en PDF adjunta a este email.
    </p>
    """

    payload = {
        "from": settings.ORDER_FROM_EMAIL,
        "to": [recipient],
        "subject": f"Remito #{invoice.invoice_number}",
        "html": _base_email_wrapper(content),
        "attachments": [_build_invoice_attachment(invoice)],
    }

    _post_email_payload(payload)

def send_sales_quote_customer_email(
    order: Order,
    quote: SalesQuote,
) -> None:
    """
    Envía el presupuesto de venta al cliente cuando el pedido (con
    document_type='sales_quote') pasa a 'preparing'.
    Solo se envía si hay email del cliente.
    """
    if not _is_email_enabled():
        raise RuntimeError("Email no configurado. Faltan variables de entorno.")

    recipient = order.customer_email
    if not recipient:
        return

    items_html = _build_items_html(order)

    content = f"""
    <h2 style="margin:0 0 4px;font-size:22px;font-weight:600;color:#111827;">
      Tu presupuesto está listo
    </h2>
    <p style="margin:0 0 24px;font-size:15px;color:#6b7280;">
      Hola <strong>{order.customer_name}</strong>, adjuntamos el presupuesto
      correspondiente a tu pedido.
    </p>

    <div style="background:#f9fafb;border-radius:8px;padding:12px 16px;
                margin-bottom:16px;">
      <table style="width:100%;">
        <tr>
          <td style="font-size:13px;color:#6b7280;">N° Presupuesto</td>
          <td style="font-size:14px;font-weight:600;color:#111827;
                     text-align:right;">{quote.quote_number}</td>
        </tr>
        <tr>
          <td style="font-size:13px;color:#6b7280;padding-top:4px;">Fecha</td>
          <td style="font-size:14px;color:#374151;text-align:right;
                     padding-top:4px;">{quote.quote_date}</td>
        </tr>
      </table>
    </div>

    {items_html}

    <table style="width:100%;margin-top:8px;">
      <tr>
        <td style="font-size:15px;color:#374151;font-weight:500;">Total</td>
        <td style="font-size:18px;font-weight:700;color:#111827;text-align:right;">
          {_format_currency(quote.total_amount, quote.currency)}
        </td>
      </tr>
    </table>

    <p style="margin:24px 0 0;font-size:13px;color:#9ca3af;">
      Encontrás el presupuesto en PDF adjunto a este email.
    </p>
    """

    payload = {
        "from": settings.ORDER_FROM_EMAIL,
        "to": [recipient],
        "subject": f"Presupuesto #{quote.quote_number}",
        "html": _base_email_wrapper(content),
        "attachments": [_build_sales_quote_attachment(quote)],
    }

    _post_email_payload(payload)

def utcnow():
    from datetime import datetime, timezone
    return datetime.now(timezone.utc)