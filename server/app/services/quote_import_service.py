from __future__ import annotations

import os
import re
import tempfile
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Optional

import pdfplumber
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.sales_rep_model import SalesRep
from app.schemas.purchase_quote_schema import PurchaseQuoteCreate, PurchaseQuoteItemCreate
from app.schemas.quote_import_schema import (
    ParsedQuoteItem,
    PurchaseQuoteImportCommitRequest,
    PurchaseQuoteImportPreviewResponse,
    SalesQuoteImportCommitRequest,
    SalesQuoteImportPreviewResponse,
)
from app.schemas.sales_quote_schema import SalesQuoteCreate, SalesQuoteItemCreate
from app.services.purchase_quote_service import PurchaseQuoteService
from app.services.sales_quote_service import SalesQuoteService

# ---------------------------------------------------------------------------
# Parsing del formato de presupuesto (ej. documentos tipo "BRAÑAS"):
#
#   21/9/2026                                          <- fecha
#   BRAÑAS                                              <- casa/sucursal emisora
#   CONSUMIDOR FINAL                                    <- cliente (o nombre proveedor en compra)
#   EFECTIVO                                            <- forma de pago
#   20 PHILIP MORRIS BOX - MASSALIN 5.720,0000 0,00 114.400,00
#   ...                                                  <- cant. producto p.unit desc. total
#
# El nombre de producto a veces se corta y la marca queda en la línea
# siguiente (ej. "... UVA MENTOL X20 -" seguido de "ESPERT").
# ---------------------------------------------------------------------------

_DATE_RE = re.compile(r"^(\d{1,2})/(\d{1,2})/(\d{4})$")
_ITEM_RE = re.compile(
    r"^(\d+)\s+(.+?)\s+([\d.]+,\d{2,4})\s+([\d.]+,\d{2})\s+([\d.]+,\d{2})$"
)
_TOTAL_RE = re.compile(r"^[\d.]+,\d{2}$")
_PAYMENT_KEYWORDS = {
    "EFECTIVO", "TRANSFERENCIA", "CUENTA CORRIENTE", "TARJETA",
    "TARJETA DE CREDITO", "TARJETA DE DEBITO", "CHEQUE", "MERCADO PAGO",
}


def _parse_amount(raw: str) -> Optional[Decimal]:
    try:
        return Decimal(raw.replace(".", "").replace(",", "."))
    except InvalidOperation:
        return None


def _parse_date(raw: str) -> Optional[date]:
    m = _DATE_RE.match(raw.strip())
    if not m:
        return None
    day, month, year = (int(g) for g in m.groups())
    try:
        return date(year, month, day)
    except ValueError:
        return None


def _extract_lines(source: bytes) -> list[str]:
    """Extrae todas las líneas de texto del PDF (bytes) usando pdfplumber."""
    tmp_fd, tmp_path = tempfile.mkstemp(suffix=".pdf")
    lines: list[str] = []
    try:
        os.write(tmp_fd, source)
        os.close(tmp_fd)
        with pdfplumber.open(tmp_path) as pdf:
            for page in pdf.pages:
                raw_text = page.extract_text() or ""
                for line in raw_text.split("\n"):
                    line = line.strip()
                    if line:
                        lines.append(line)
    finally:
        os.unlink(tmp_path)
    return lines


def _parse_quote_pdf(source: bytes) -> dict:
    """
    Parsea el PDF y devuelve un dict genérico con:
    quote_date, header_lines (metadata antes del primer ítem),
    items (lista de dicts), total_amount (suma de subtotales), warnings.
    """
    lines = _extract_lines(source)
    warnings: list[str] = []

    quote_date: Optional[date] = None
    header_lines: list[str] = []
    items: list[dict] = []

    i = 0
    n = len(lines)
    in_header = True

    while i < n:
        line = lines[i]

        if quote_date is None:
            parsed = _parse_date(line)
            if parsed:
                quote_date = parsed
                i += 1
                continue

        item_match = _ITEM_RE.match(line)
        if item_match:
            in_header = False
            qty_str, name, price_str, subtotal_str = item_match.groups()

            # Si el nombre corta con "-" al final, la marca suele quedar
            # en la línea siguiente (wrap de columna del PDF de origen).
            if name.endswith("-") and i + 1 < n:
                next_line = lines[i + 1]
                if not _ITEM_RE.match(next_line) and not _TOTAL_RE.match(next_line) and next_line != "$":
                    name = f"{name} {next_line}".strip()
                    i += 1

            unit_price = _parse_amount(price_str)
            subtotal = _parse_amount(subtotal_str)
            quantity = int(qty_str)

            item_warnings = []
            if unit_price is None:
                item_warnings.append("No se pudo interpretar el precio unitario")
            if subtotal is None:
                item_warnings.append("No se pudo interpretar el subtotal")

            expected_subtotal = None
            if unit_price is not None:
                expected_subtotal = (unit_price * quantity)
                if subtotal is not None and abs(expected_subtotal - subtotal) > Decimal("0.5"):
                    item_warnings.append(
                        "El subtotal impreso no coincide con cantidad × precio − descuento"
                    )

            items.append({
                "product_name": name.strip(),
                "quantity": quantity,
                "unit_price": unit_price,
                "subtotal": subtotal if subtotal is not None else expected_subtotal,
                "confidence": 1.0 if not item_warnings else 0.6,
                "warnings": item_warnings,
            })
            i += 1
            continue

        if in_header and line != "$" and not _TOTAL_RE.match(line):
            header_lines.append(line)

        i += 1

    if quote_date is None:
        warnings.append("No se pudo detectar la fecha del presupuesto en el PDF")

    if not items:
        warnings.append("No se detectaron ítems en el PDF; revisar el formato del documento")

    total_amount = sum((it["subtotal"] or Decimal("0.00")) for it in items) or None

    return {
        "quote_date": quote_date,
        "header_lines": header_lines,
        "items": items,
        "total_amount": total_amount,
        "raw_text": "\n".join(lines),
        "warnings": warnings,
    }


def _split_header_purchase(header_lines: list[str]) -> tuple[Optional[str], Optional[str]]:
    """
    De las líneas de encabezado (antes del primer ítem), intenta separar
    nombre del proveedor. Asume que la última línea que no es una forma
    de pago conocida corresponde al proveedor/emisor.
    """
    candidates = [l for l in header_lines if l.upper() not in _PAYMENT_KEYWORDS]
    supplier_name = candidates[-1] if candidates else None
    return supplier_name, None


def _split_header_sales(header_lines: list[str]) -> tuple[Optional[str], Optional[str]]:
    """
    De las líneas de encabezado, separa cliente y forma de pago.
    La forma de pago es la última línea si coincide con una palabra
    clave conocida (EFECTIVO, TRANSFERENCIA, etc). El cliente es la
    línea anterior a esa (o la última restante si no hay forma de pago
    detectada), ignorando la primera línea (casa/sucursal emisora).
    """
    remaining = list(header_lines)
    payment_method = None

    if remaining and remaining[-1].upper() in _PAYMENT_KEYWORDS:
        payment_method = remaining.pop().upper()

    client_name = None
    if len(remaining) >= 2:
        client_name = remaining[-1]
    elif remaining:
        client_name = remaining[-1]

    return client_name, payment_method


class QuoteImportService:
    """
    Servicio de importación (preview + commit) para presupuestos de
    compra y venta a partir de un PDF con el formato de referencia.
    """

    def __init__(self, db: Session):
        self.db = db
        self.purchase_quote_service = PurchaseQuoteService(db)
        self.sales_quote_service = SalesQuoteService(db)

    # ------------------------------------------------------------------ #
    #  Presupuesto de compra
    # ------------------------------------------------------------------ #

    def preview_purchase_quote(self, file_bytes: bytes) -> PurchaseQuoteImportPreviewResponse:
        parsed = _parse_quote_pdf(file_bytes)
        supplier_name, _ = _split_header_purchase(parsed["header_lines"])

        items = [
            ParsedQuoteItem(
                product_name=it["product_name"],
                quantity=it["quantity"],
                unit_cost=it["unit_price"],
                subtotal=it["subtotal"],
                confidence=it["confidence"],
                warnings=it["warnings"],
            )
            for it in parsed["items"]
        ]

        return PurchaseQuoteImportPreviewResponse(
            supplier_name=supplier_name,
            supplier_tax_id=None,
            quote_number=None,
            quote_date=parsed["quote_date"],
            total_amount=parsed["total_amount"],
            items=items,
            raw_text=parsed["raw_text"],
            warnings=parsed["warnings"],
            errors=[],
        )

    def commit_purchase_quote(
        self,
        data: PurchaseQuoteImportCommitRequest,
        current_user: Optional[SalesRep],
    ):
        if not data.items:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No hay ítems para confirmar",
            )

        items = [
            PurchaseQuoteItemCreate(
                product_id=item.product_id,
                product_name=item.product_name or "Producto sin nombre",
                product_sku=item.product_sku,
                quantity=item.quantity,
                unit_cost=item.unit_cost or Decimal("0.00"),
            )
            for item in data.items
        ]

        create_data = PurchaseQuoteCreate(
            supplier_id=data.supplier_id,
            supplier_name=data.supplier_name,
            supplier_tax_id=data.supplier_tax_id,
            quote_number=data.quote_number,
            quote_date=data.quote_date,
            valid_until=data.valid_until,
            notes=data.notes,
            items=items,
            force=data.force,
        )

        return self.purchase_quote_service.create(create_data, current_user)

    # ------------------------------------------------------------------ #
    #  Presupuesto de venta
    # ------------------------------------------------------------------ #

    def preview_sales_quote(self, file_bytes: bytes) -> SalesQuoteImportPreviewResponse:
        parsed = _parse_quote_pdf(file_bytes)
        client_name, payment_method = _split_header_sales(parsed["header_lines"])

        items = [
            ParsedQuoteItem(
                product_name=it["product_name"],
                quantity=it["quantity"],
                unit_price=it["unit_price"],
                subtotal=it["subtotal"],
                confidence=it["confidence"],
                warnings=it["warnings"],
            )
            for it in parsed["items"]
        ]

        return SalesQuoteImportPreviewResponse(
            client_name=client_name,
            client_tax_id=None,
            payment_method=payment_method,
            quote_number=None,
            quote_date=parsed["quote_date"],
            total_amount=parsed["total_amount"],
            items=items,
            raw_text=parsed["raw_text"],
            warnings=parsed["warnings"],
            errors=[],
        )

    def commit_sales_quote(
        self,
        data: SalesQuoteImportCommitRequest,
        current_user: Optional[SalesRep],
    ):
        if not data.items:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No hay ítems para confirmar",
            )

        items = [
            SalesQuoteItemCreate(
                product_id=item.product_id,
                product_name=item.product_name or "Producto sin nombre",
                product_sku=item.product_sku,
                quantity=item.quantity,
                unit_price=item.unit_price or Decimal("0.00"),
            )
            for item in data.items
        ]

        create_data = SalesQuoteCreate(
            client_id=data.client_id,
            client_name=data.client_name,
            client_tax_id=data.client_tax_id,
            payment_method=data.payment_method,
            quote_number=data.quote_number,
            quote_date=data.quote_date,
            valid_until=data.valid_until,
            notes=data.notes,
            items=items,
            force=data.force,
        )

        return self.sales_quote_service.create(create_data, current_user)