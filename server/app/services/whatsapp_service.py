from __future__ import annotations
import json
import mimetypes
import re
import uuid
from urllib import error, request
import phonenumbers
from app.core.config import get_settings
from app.models.order_model import Order
from app.models.sales_invoice_model import SalesInvoice
from app.services.order_pdf_service import build_order_pdf
from app.services.sales_invoice_pdf_service import build_sales_invoice_pdf

settings = get_settings()

GRAPH_API_VERSION = "v21.0"

def _is_whatsapp_enabled() -> bool:
    return bool(settings.WHATSAPP_ACCESS_TOKEN and settings.WHATSAPP_PHONE_NUMBER_ID)

def _graph_url(path: str) -> str:
    return f"https://graph.facebook.com/{GRAPH_API_VERSION}/{settings.WHATSAPP_PHONE_NUMBER_ID}{path}"

def _normalize_phone(raw_phone: str) -> str:
    """
    Convierte un teléfono argentino "local" (ej: 3756513101, sin 0 ni 15)
    al formato que efectivamente espera la API de WhatsApp para números
    de Argentina: 54 + código de área + 15 + número local.

    Esto NO es el formato E.164 estándar (que sería 54 9 <área><número>).
    Es un quirk histórico de Meta/WhatsApp específico de Argentina: la
    API todavía espera el viejo prefijo "15" en vez del "9" internacional,
    sin importar que el número real del cliente use el "9" en cualquier
    otro contexto (SMS, llamadas, etc).

    Usamos `phonenumbers` (la librería de Google) para separar
    correctamente el código de área del número local, porque varía
    entre 2 y 4 dígitos según la provincia (ej: 11 Buenos Aires,
    351 Córdoba, 3756 Eldorado) y adivinarlo a mano no es confiable.
    """
    digits = re.sub(r"[^\d]", "", raw_phone or "")

    if not digits:
        return digits

    # Solo intentamos transformar formatos de entrada "crudos" conocidos:
    # 10 dígitos (local), 12 (54 + local) o 13 (54 + 9 + local). Cualquier
    # otra longitud (ej: 14 dígitos, ya con el "15" insertado) se deja
    # intacta para no romper un número que ya estaba bien formateado.
    if len(digits) not in (10, 12, 13):
        return digits

    candidate = digits
    if candidate.startswith("54") and len(candidate) in (12, 13):
        candidate = candidate[2:]
        if candidate.startswith("9"):
            candidate = candidate[1:]

    try:
        parsed = phonenumbers.parse(candidate, "AR")
        if not phonenumbers.is_valid_number(parsed):
            return digits

        national = phonenumbers.national_significant_number(parsed)
        area_len = phonenumbers.length_of_national_destination_code(parsed)

        if not area_len:
            return f"54{national}"

        area_code = national[:area_len]
        local_number = national[area_len:]
        return f"54{area_code}15{local_number}"

    except phonenumbers.NumberParseException:
        return digits

def phones_match(phone_a: str, phone_b: str) -> bool:
    """
    Compara dos teléfonos ignorando diferencias de formato (código de
    país, el 9, el 15, espacios, guiones, etc). Se usa para validar
    que quien responde un botón de WhatsApp es realmente el dueño del
    pedido, comparando el 'from' del webhook contra el customer_phone
    guardado en la orden.

    Compara solo los últimos 10 dígitos (el número local argentino),
    que es la parte que identifica al abonado sin ambigüedad de
    formato entre "5493756513101" (wa_id real) y "54375615513101"
    (formato que usa la API para envíos).
    """
    digits_a = re.sub(r"[^\d]", "", phone_a or "")
    digits_b = re.sub(r"[^\d]", "", phone_b or "")

    if len(digits_a) < 10 or len(digits_b) < 10:
        return False

    return digits_a[-10:] == digits_b[-10:]

def _post_whatsapp_json(payload: dict) -> dict:
    if not _is_whatsapp_enabled():
        raise RuntimeError("WhatsApp no configurado. Faltan variables de entorno.")

    req = request.Request(
        url=_graph_url("/messages"),
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {settings.WHATSAPP_ACCESS_TOKEN}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with request.urlopen(req, timeout=20) as response:
            body = response.read().decode("utf-8")
            if response.getcode() >= 300:
                raise RuntimeError(f"WhatsApp respondió {response.getcode()}: {body}")
            return json.loads(body)

    except error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"Error HTTP de WhatsApp {exc.code}: {body}") from exc
    except error.URLError as exc:
        raise RuntimeError(f"No se pudo conectar con WhatsApp: {exc.reason}") from exc

def _upload_media(pdf_bytes: bytes, filename: str) -> str:
    """
    Sube un PDF al servidor de medios de Meta y devuelve el media_id
    necesario para poder mandarlo como documento en un mensaje.
    Se arma el multipart/form-data a mano para no sumar dependencias.
    """
    if not _is_whatsapp_enabled():
        raise RuntimeError("WhatsApp no configurado. Faltan variables de entorno.")

    boundary = uuid.uuid4().hex
    content_type = mimetypes.guess_type(filename)[0] or "application/pdf"

    fields = {
        "messaging_product": "whatsapp",
        "type": content_type,
    }

    body = b""
    for key, value in fields.items():
        body += (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="{key}"\r\n\r\n'
            f"{value}\r\n"
        ).encode("utf-8")

    body += (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
        f"Content-Type: {content_type}\r\n\r\n"
    ).encode("utf-8")
    body += pdf_bytes
    body += f"\r\n--{boundary}--\r\n".encode("utf-8")

    req = request.Request(
        url=_graph_url("/media"),
        data=body,
        headers={
            "Authorization": f"Bearer {settings.WHATSAPP_ACCESS_TOKEN}",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        },
        method="POST",
    )

    try:
        with request.urlopen(req, timeout=30) as response:
            resp_body = response.read().decode("utf-8")
            if response.getcode() >= 300:
                raise RuntimeError(f"WhatsApp (media) respondió {response.getcode()}: {resp_body}")
            data = json.loads(resp_body)
            media_id = data.get("id")
            if not media_id:
                raise RuntimeError(f"WhatsApp no devolvió media_id: {resp_body}")
            return media_id

    except error.HTTPError as exc:
        body_err = exc.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"Error HTTP subiendo media a WhatsApp {exc.code}: {body_err}") from exc
    except error.URLError as exc:
        raise RuntimeError(f"No se pudo conectar con WhatsApp: {exc.reason}") from exc

def _format_currency(amount, currency: str = "ARS") -> str:
    try:
        return f"{currency} {float(amount):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except (TypeError, ValueError):
        return f"{currency} -"

def send_order_customer_whatsapp(order: Order) -> None:
    """
    Manda el mensaje de 'pedido recibido' con botones interactivos para
    que el cliente pueda cancelar, modificar o confirmar el pedido.

    IMPORTANTE: si este es el primer mensaje que le mandás al cliente
    (o pasaron más de 24hs desde su último mensaje a tu número), Meta
    exige que se envíe como *template* aprobado en vez de un mensaje
    interactivo libre como este. Este método sirve para responder
    dentro de la ventana de 24hs (por ejemplo, si el cliente ya te
    escribió para hacer el pedido por WhatsApp).
    """
    if not order.customer_phone:
        return

    items_summary = "\n".join(
        f"• {item.quantity}x {item.product_name_snapshot}"
        for item in order.items
    )

    body_text = (
        f"Hola {order.customer_name},"
        f"Confirmamos que recibimos tu pedido *#{order.id}*:\n\n"
        f"{items_summary}\n\n"
        f"Total: {_format_currency(order.total_amount, order.currency)}\n\n"
        f"¿Qué querés hacer?\n\n"
        f"_Este es un mensaje automático de nuestro asistente de WhatsApp._"
    )

    payload = {
        "messaging_product": "whatsapp",
        "to": _normalize_phone(order.customer_phone),
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {"text": body_text},
            "action": {
                "buttons": [
                    {
                        "type": "reply",
                        "reply": {"id": f"confirm_order:{order.id}:{order.tenant_id}", "title": "Confirmar"},
                    },
                    {
                        "type": "reply",
                        "reply": {"id": f"modify_order:{order.id}:{order.tenant_id}", "title": "Modificar"},
                    },
                    {
                        "type": "reply",
                        "reply": {"id": f"cancel_order:{order.id}:{order.tenant_id}", "title": "Cancelar"},
                    },
                ]
            },
        },
    }

    _post_whatsapp_json(payload)

def send_order_admin_whatsapp(order: Order) -> None:
    """Aviso de texto simple al número del negocio cuando entra un pedido nuevo."""
    if not settings.WHATSAPP_ADMIN_PHONE:
        return

    delivery_label = "Envío a domicilio" if order.delivery_type == "delivery" else "Retiro en local"

    body_text = (
        f"Nuevo pedido #{order.id}\n"
        f"Cliente: {order.customer_name}\n"
        f"Tel: {order.customer_phone or '—'}\n"
        f"Entrega: {delivery_label}\n"
        f"Total: {_format_currency(order.total_amount, order.currency)}"
    )

    payload = {
        "messaging_product": "whatsapp",
        "to": _normalize_phone(settings.WHATSAPP_ADMIN_PHONE),
        "type": "text",
        "text": {"body": body_text},
    }

    _post_whatsapp_json(payload)

def send_order_status_whatsapp(order: Order, message: str) -> None:
    """Mensaje de texto simple para avisos de cambio de estado (shipped, delivered, etc)."""
    if not order.customer_phone:
        return

    payload = {
        "messaging_product": "whatsapp",
        "to": _normalize_phone(order.customer_phone),
        "type": "text",
        "text": {"body": message},
    }

    _post_whatsapp_json(payload)

def send_invoice_customer_whatsapp(order: Order, invoice: SalesInvoice) -> None:
    """
    Sube el remito en PDF y la envía como documento por WhatsApp.
    Se dispara cuando el pedido pasa a 'preparing' (listo para
    despachar o retirar), igual que send_invoice_customer_email.
    """
    if not order.customer_phone:
        return

    pdf_bytes = build_sales_invoice_pdf(invoice)
    filename = f"remito-{invoice.invoice_number}.pdf"
    media_id = _upload_media(pdf_bytes, filename)

    payload = {
        "messaging_product": "whatsapp",
        "to": _normalize_phone(order.customer_phone),
        "type": "document",
        "document": {
            "id": media_id,
            "filename": filename,
            "caption": f"Remito #{invoice.invoice_number} — {_format_currency(invoice.total_amount, invoice.currency)}",
        },
    }

    _post_whatsapp_json(payload)