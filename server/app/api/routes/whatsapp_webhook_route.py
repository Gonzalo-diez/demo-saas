import hashlib
import hmac
import logging

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, Response, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.order_edit_token import create_order_edit_token
from app.db.base import get_db_with_commit
from app.db.tenant_context import set_tenant
from app.models.tenant_model import Tenant
from app.services.order_service import OrderService
from app.services import whatsapp_service

logger = logging.getLogger("whatsapp_webhook")
settings = get_settings()

router = APIRouter(prefix="/webhooks/whatsapp", tags=["WhatsApp Webhook"])


def _verify_signature(raw_body: bytes, signature_header: str | None) -> bool:
    """
    Verifica que el payload realmente venga de Meta, comparando el
    X-Hub-Signature-256 contra un HMAC-SHA256 calculado con el App Secret.
    Sin APP_SECRET solo se acepta en entornos de desarrollo: en producción un
    webhook sin firma permitiría a cualquiera simular mensajes de clientes.
    """
    if not settings.WHATSAPP_APP_SECRET:
        return settings.ENV.lower() in ("dev", "development", "test", "local")

    if not signature_header or not signature_header.startswith("sha256="):
        return False

    expected = hmac.new(
        settings.WHATSAPP_APP_SECRET.encode("utf-8"),
        raw_body,
        hashlib.sha256,
    ).hexdigest()

    received = signature_header.removeprefix("sha256=")
    return hmac.compare_digest(expected, received)


@router.get("")
def verify_webhook(
    hub_mode: str = Query(default="", alias="hub.mode"),
    hub_verify_token: str = Query(default="", alias="hub.verify_token"),
    hub_challenge: str = Query(default="", alias="hub.challenge"),
):
    """
    Endpoint que Meta llama una sola vez al configurar el webhook en
    developers.facebook.com para confirmar que el servidor es tuyo.
    """
    if not settings.WHATSAPP_VERIFY_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="WHATSAPP_VERIFY_TOKEN no está configurado.",
        )

    if hub_mode == "subscribe" and hub_verify_token == settings.WHATSAPP_VERIFY_TOKEN:
        return Response(content=hub_challenge, media_type="text/plain")

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Token de verificación inválido.",
    )


def _extract_events(payload: dict) -> list[dict]:
    """
    Recorre la estructura del payload de Meta y devuelve una lista
    plana de eventos simplificados: mensajes de texto, respuestas a
    botones interactivos y actualizaciones de estado (sent/delivered/read).
    """
    events: list[dict] = []

    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            value = change.get("value", {})

            for message in value.get("messages", []):
                from_number = message.get("from")
                msg_type = message.get("type")

                if msg_type == "interactive":
                    interactive = message.get("interactive", {})
                    button_reply = interactive.get("button_reply")
                    list_reply = interactive.get("list_reply")

                    if button_reply:
                        events.append({
                            "kind": "button_reply",
                            "from": from_number,
                            "message_id": message.get("id"),
                            "button_id": button_reply.get("id"),
                            "button_title": button_reply.get("title"),
                        })
                    elif list_reply:
                        events.append({
                            "kind": "list_reply",
                            "from": from_number,
                            "message_id": message.get("id"),
                            "option_id": list_reply.get("id"),
                            "option_title": list_reply.get("title"),
                        })

                elif msg_type == "text":
                    events.append({
                        "kind": "text",
                        "from": from_number,
                        "message_id": message.get("id"),
                        "text": message.get("text", {}).get("body"),
                    })

                else:
                    events.append({
                        "kind": "unhandled_message_type",
                        "from": from_number,
                        "message_id": message.get("id"),
                        "message_type": msg_type,
                    })

            for status_update in value.get("statuses", []):
                events.append({
                    "kind": "status_update",
                    "message_id": status_update.get("id"),
                    "status": status_update.get("status"),
                    "recipient": status_update.get("recipient_id"),
                    "errors": status_update.get("errors", []),
                })

    return events


def _parse_button_id(button_id: str) -> tuple[str, int, int] | None:
    """
    Los botones se arman en whatsapp_service.py con el formato
    'accion:order_id:tenant_id' (ej: 'cancel_order:43:2'). Acá lo separamos.
    Devuelve None si el formato no es el esperado.
    """
    if not button_id:
        return None

    parts = button_id.split(":")
    if len(parts) != 3 or not parts[1].isdigit() or not parts[2].isdigit():
        return None

    return parts[0], int(parts[1]), int(parts[2])


def _handle_button_reply(event: dict, db: Session) -> None:
    parsed = _parse_button_id(event.get("button_id", ""))

    if not parsed:
        logger.warning("[WhatsApp webhook] button_id con formato inesperado: %s", event)
        return

    action, order_id, tenant_id = parsed

    # El webhook es público: el tenant sale del id del botón (lo armamos nosotros
    # al enviar el mensaje y viaja dentro del payload firmado por Meta).
    tenant = db.get(Tenant, tenant_id)
    if tenant is None or not tenant.is_active:
        logger.warning("[WhatsApp webhook] tenant %s inexistente o inactivo", tenant_id)
        return
    set_tenant(db, tenant_id)

    order_service = OrderService(db)

    try:
        order = order_service.get_order(order_id)

        if not order:
            logger.warning("[WhatsApp webhook] pedido #%s no encontrado", order_id)
            return

        sender_phone = event.get("from", "")

        if not order.customer_phone or not whatsapp_service.phones_match(sender_phone, order.customer_phone):
            logger.warning(
                "[WhatsApp webhook] intento de modificar pedido #%s desde un número que no coincide "
                "(from=%s, order.customer_phone=%s)",
                order_id, sender_phone, order.customer_phone,
            )
            return

        if action == "cancel_order":
            updated_order = order_service.update_order_status(order_id, "cancelled")
            whatsapp_service.send_order_status_whatsapp(
                updated_order,
                f"Listo, cancelamos tu pedido #{updated_order.id}. "
                f"Si fue un error o querés hacer un pedido nuevo, avisanos.",
            )

        elif action == "confirm_order":
            updated_order = order_service.update_order_status(
                order_id,
                "preparing",
            )
            whatsapp_service.send_order_status_whatsapp(
                updated_order,
                f"¡Perfecto! Ya arrancamos a preparar tu pedido #{updated_order.id}.",
            )

        elif action == "modify_order":
            edit_token = create_order_edit_token(order.id, order.tenant_id)
            edit_url = f"{settings.FRONTEND_ORIGIN}/orders/{order.id}/editar?token={edit_token}"
            whatsapp_service.send_order_status_whatsapp(
                order,
                f"Para modificar tu pedido #{order.id}, entrá acá: {edit_url}\n\n"
                f"El link es válido por 48hs. Si preferís, contanos por acá "
                f"qué necesitás y te ayudamos.",
            )

        else:
            logger.warning("[WhatsApp webhook] acción desconocida: %s", action)

    except ValueError as exc:
        # Transición de estado inválida (ej: ya estaba cancelado/entregado)
        logger.warning("[WhatsApp webhook] no se pudo aplicar '%s' al pedido #%s: %s", action, order_id, exc)
        whatsapp_service.send_order_status_whatsapp(
            order,
            f"No pudimos aplicar ese cambio a tu pedido #{order_id} "
            f"(puede que ya esté en otro estado). Contactanos si tenés dudas.",
        )

def _dispatch_event(event: dict, db: Session) -> None:
    """
    Punto único de entrada para procesar cada evento entrante.
    """
    logger.info("[WhatsApp webhook] evento recibido: %s", event)

    if event.get("kind") == "status_update":
        if event.get("status") == "failed":
            logger.error(
                "[WhatsApp webhook] mensaje FALLIDO "
                "message_id=%s recipient=%s errors=%s",
                event.get("message_id"),
                event.get("recipient"),
                event.get("errors"),
            )

        return

    if event.get("kind") == "button_reply":
        _handle_button_reply(event, db)

@router.post("")
async def receive_webhook(
    request: Request,
    x_hub_signature_256: str | None = Header(default=None),
    db: Session = Depends(get_db_with_commit),
):
    raw_body = await request.body()

    if not _verify_signature(raw_body, x_hub_signature_256):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Firma inválida.",
        )

    payload = await request.json()

    try:
        events = _extract_events(payload)
        for event in events:
            _dispatch_event(event, db)
    except Exception:
        # Nunca devolvemos error a Meta por una falla interna de parseo:
        # si respondemos != 200, Meta reintenta el webhook varias veces.
        logger.exception("[WhatsApp webhook] error procesando payload")

    return Response(status_code=status.HTTP_200_OK)