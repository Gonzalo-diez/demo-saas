from __future__ import annotations
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from io import BytesIO
import json
import re
from unittest import result
import cv2
import fitz
import numpy as np
import pdfplumber
from fastapi import HTTPException, UploadFile, status
from pyzbar.pyzbar import decode as decode_qr
from sqlalchemy.orm import Session
from app.models.sales_rep_model import SalesRep
from app.repositories.client_repository import ClientRepository
from app.repositories.product_repository import ProductRepository
from app.repositories.supplier_repository import SupplierRepository
from app.schemas.supplier_schema import SupplierCreate
from app.schemas.invoice_import_schema import (
    InvoiceItemCommit,
    ParsedInvoiceItem,
    PurchaseInvoiceImportCommitRequest,
    PurchaseInvoiceImportPreviewResponse,
    SalesInvoiceImportCommitRequest,
    SalesInvoiceImportPreviewResponse,
)
from app.schemas.purchase_invoice_schema import (
    PurchaseInvoiceCreate,
    PurchaseInvoiceItemCreate,
)
from app.schemas.sales_invoice_schema import (
    SalesInvoiceCreate,
    SalesInvoiceItemCreate,
)
from app.services.purchase_invoice_service import PurchaseInvoiceService
from app.services.sales_invoice_service import SalesInvoiceService

class InvoiceImportService:
    def __init__(self, db: Session):
        self.product_repo = ProductRepository(db)
        self.client_repo = ClientRepository(db)
        self.supplier_repo = SupplierRepository(db)
        self.purchase_invoice_service = PurchaseInvoiceService(db)
        self.sales_invoice_service = SalesInvoiceService(db)

    async def preview_purchase_file(
        self,
        file: UploadFile,
    ) -> PurchaseInvoiceImportPreviewResponse:
        self._validate_file_type(file)

        file_bytes = await file.read()
        raw_text = self._extract_text_from_pdf(file_bytes)
        extracted_tables = self._extract_tables_from_pdf(file_bytes)
        qr_payload = self._extract_qr_payload_from_pdf(file_bytes)

        warnings: list[str] = []
        errors: list[str] = []

        header_data = self._parse_invoice_header(raw_text, qr_payload, is_purchase=True)
        items = self._parse_purchase_items(extracted_tables, raw_text)

        if not raw_text.strip():
            errors.append("No se pudo extraer texto del PDF")

        if not items:
            warnings.append(
                "No se pudieron detectar items de compra de forma confiable. "
                "Deberás cargarlos o corregirlos manualmente."
            )

        if qr_payload is None:
            warnings.append("No se pudo leer el QR AFIP del PDF")

        return PurchaseInvoiceImportPreviewResponse(
            supplier_name=header_data.get("supplier_name"),
            supplier_tax_id=header_data.get("supplier_tax_id"),
            invoice_number=header_data.get("invoice_number"),
            invoice_date=header_data.get("invoice_date"),
            total_amount=header_data.get("total_amount"),
            items=items,
            raw_text=raw_text,
            warnings=warnings,
            errors=errors,
        )

    def commit_purchase(
        self,
        data: PurchaseInvoiceImportCommitRequest,
        current_user: SalesRep | None,
    ):
        if not data.items:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Debes enviar al menos un item para importar el remito de compra",
            )

        supplier = None

        if data.supplier_tax_id:
            supplier = self.supplier_repo.get_by_tax_id(data.supplier_tax_id)

        if not supplier and data.supplier_name:
            supplier = self.supplier_repo.get_by_name(data.supplier_name)

        if not supplier and (data.supplier_name or data.supplier_tax_id):
            supplier = self.supplier_repo.create(
                SupplierCreate(
                    name=(data.supplier_name or "").strip() or "Proveedor sin nombre",
                    tax_id=(data.supplier_tax_id or "").strip() or None,
                    email=None,
                    phone=None,
                    address=None,
                    is_active=True,
                )
            )

        supplier_id = supplier.id if supplier else None

        purchase_items: list[PurchaseInvoiceItemCreate] = []

        for item in data.items:
            product_name = (item.product_name or "").strip()
            product_sku = (item.product_sku or "").strip() or None

            if not product_name:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Todos los items deben tener product_name",
                )

            if item.quantity <= 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Cantidad inválida para item '{product_name}'",
                )

            unit_cost = self._pick_decimal_value(item.unit_cost, "unit_cost", product_name)

            # Buscar producto existente por SKU y, si no matchea, por
            # nombre: evita crear un producto duplicado cuando el remito
            # trae un producto que ya está cargado con otro SKU (o sin SKU).
            matched_product = self.product_repo.find_by_sku_or_name(product_sku, product_name)

            purchase_items.append(
                PurchaseInvoiceItemCreate(
                    product_id=matched_product.id if matched_product else None,
                    product_name=product_name,
                    product_sku=product_sku,
                    quantity=item.quantity,
                    unit_cost=unit_cost,
                )
            )

        payload = PurchaseInvoiceCreate(
            supplier_id=supplier_id,
            supplier_name=supplier.name if supplier else ((data.supplier_name or "").strip() or "Proveedor desconocido"),
            supplier_tax_id=supplier.tax_id if supplier else ((data.supplier_tax_id or "").strip() or None),
            invoice_number=data.invoice_number.strip(),
            invoice_date=data.invoice_date,
            notes=(data.notes or "").strip() or None,
            items=purchase_items,
            force=data.force,
        )

        return self.purchase_invoice_service.create(payload, current_user)

    async def preview_sales_file(
        self,
        file: UploadFile,
    ) -> SalesInvoiceImportPreviewResponse:
        self._validate_file_type(file)

        file_bytes = await file.read()
        raw_text = self._extract_text_from_pdf(file_bytes)
        extracted_tables = self._extract_tables_from_pdf(file_bytes)
        qr_payload = self._extract_qr_payload_from_pdf(file_bytes)

        warnings: list[str] = []
        errors: list[str] = []

        header_data = self._parse_invoice_header(raw_text, qr_payload, is_purchase=False)
        items = self._parse_sales_items(extracted_tables, raw_text)

        # Enriquecer unit_cost desde la DB buscando cada producto por nombre
        for item in items:
            if item.product_name:
                matched = self.product_repo.get_product_by_name(item.product_name)
                if matched and matched.unit_cost is not None:
                    item.unit_cost = matched.unit_cost

        if not raw_text.strip():
            errors.append("No se pudo extraer texto del PDF")

        if not items:
            warnings.append(
                "No se pudieron detectar items de venta de forma confiable. "
                "Deberás vincularlos manualmente a productos existentes."
            )

        if qr_payload is None:
            warnings.append("No se pudo leer el QR AFIP del PDF")

        return SalesInvoiceImportPreviewResponse(
            client_name=header_data.get("client_name"),
            client_tax_id=header_data.get("client_tax_id"),
            invoice_number=header_data.get("invoice_number"),
            invoice_date=header_data.get("invoice_date"),
            total_amount=header_data.get("total_amount"),
            items=items,
            raw_text=raw_text,
            warnings=warnings,
            errors=errors,
        )

    def commit_sales(
        self,
        data: SalesInvoiceImportCommitRequest,
        current_user: SalesRep,
    ):
        if not data.items:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Debes enviar al menos un item para importar el remito de venta",
            )

        client_id = self._resolve_client_id_for_sales_import(
            client_id=data.client_id,
            client_tax_id=data.client_tax_id,
        )

        sales_items: list[SalesInvoiceItemCreate] = []

        for item in data.items:
            product_id = self._resolve_product_id_for_sales_item(item)

            sales_items.append(
                SalesInvoiceItemCreate(
                    product_id=product_id,
                    product_name=(item.product_name or "").strip(),
                    quantity=item.quantity,
                )
            )

        payload = SalesInvoiceCreate(
            client_id=client_id,
            client_branch_id=data.client_branch_id,
            sales_type="B2B",
            invoice_number=data.invoice_number.strip(),
            invoice_date=data.invoice_date,
            notes=(data.notes or "").strip() or None,
            items=sales_items,
            force=data.force,
        )

        return self.sales_invoice_service.create(payload, current_user)

    def _validate_file_type(self, file: UploadFile) -> None:
        filename = (file.filename or "").lower()

        if not filename.endswith(".pdf"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Solo se permiten archivos PDF",
            )

    def _resolve_product_id_for_sales_item(self, item: InvoiceItemCommit) -> int:
        if item.quantity <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Todos los items de venta deben tener quantity > 0",
            )

        product_id = item.product_id
        product_sku = (item.product_sku or "").strip() or None
        product_name = (item.product_name or "").strip() or None

        if product_id is not None:
            product = self.product_repo.get_product_by_id(product_id)
            if not product:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Producto con id {product_id} no encontrado",
                )
            return product.id

        if product_sku:
            product = self.product_repo.get_product_by_sku(product_sku)
            if product:
                return product.id

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "En remito de venta todos los items deben quedar vinculados a un producto existente. "
                f"No se pudo resolver el item '{product_name or product_sku or 'sin identificar'}'."
            ),
        )

    def _resolve_client_id_for_sales_import(
        self,
        client_id: int | None,
        client_tax_id: str | None,
    ) -> int:
        if client_id is not None:
            client = self.client_repo.get_by_id(client_id)
            if not client:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Cliente no encontrado",
                )
            return client.id

        if client_tax_id:
            matched = self.client_repo.get_by_tax_id(client_tax_id)
            if matched:
                return matched.id

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "No se pudo resolver el cliente para el remito de venta. "
                "Envía client_id o un client_tax_id válido."
            ),
        )

    def _pick_decimal_value(
        self,
        value: Decimal | None,
        field_name: str,
        item_label: str,
    ) -> Decimal:
        if value is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"El item '{item_label}' debe tener {field_name}",
            )

        try:
            decimal_value = Decimal(str(value))
        except (InvalidOperation, TypeError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Valor inválido en {field_name} para item '{item_label}'",
            )

        if decimal_value <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"El item '{item_label}' debe tener {field_name} > 0",
            )

        return decimal_value

    def _extract_text_from_pdf(self, file_bytes: bytes) -> str:
        try:

            pages_text: list[str] = []

            with pdfplumber.open(BytesIO(file_bytes)) as pdf:

                for page in pdf.pages:

                    text = page.extract_text(
                        x_tolerance=2,
                        y_tolerance=2,
                        layout=True,
                    ) or ""

                    # fallback usando coordenadas
                    if not text.strip():

                        words = page.extract_words(
                            x_tolerance=2,
                            y_tolerance=2,
                            keep_blank_chars=False,
                        )

                        grouped = {}

                        for word in words:

                            top = round(word["top"], 0)

                            grouped.setdefault(top, []).append(word)

                        lines = []

                        for _, row_words in sorted(grouped.items()):

                            row_words = sorted(
                                row_words,
                                key=lambda w: w["x0"],
                            )

                            line = " ".join(
                                w["text"] for w in row_words
                            )

                            lines.append(line)

                        text = "\n".join(lines)

                    pages_text.append(text)

            final_text = "\n".join(pages_text)

            final_text = self._normalize_pdf_text(
                final_text
            )

            return final_text.strip()

        except Exception:
            return ""
        
    def _normalize_pdf_text(self, text: str) -> str:
        text = text.replace("\xa0", " ")
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n{2,}", "\n", text)
        normalized_lines = []

        for line in text.splitlines():
            line = line.strip()

            if not line:
                continue

            normalized_lines.append(line)

        merged_lines: list[str] = []

        i = 0

        while i < len(normalized_lines):
            current = normalized_lines[i]
            
            if i + 1 < len(normalized_lines):
                nxt = normalized_lines[i + 1]

                current_has_money = bool(
                    re.search(r"\d+[\.,]\d{2,4}", current)
                )

                next_has_money = bool(
                    re.search(r"\d+[\.,]\d{2,4}", nxt)
                )
                
                # reconstrucción de líneas partidas
                if (
                    not current_has_money
                    and next_has_money
                    and len(current.split()) <= 8
                ):
                    merged_lines.append(
                        f"{current} {nxt}"
                    )

                    i += 2
                    continue

            merged_lines.append(current)

            i += 1

        return "\n".join(merged_lines)

    def _extract_tables_from_pdf(self, file_bytes: bytes) -> list[list[list[str]]]:
        extracted: list[list[list[str]]] = []

        try:
            with pdfplumber.open(BytesIO(file_bytes)) as pdf:
                for page in pdf.pages:
                    page_tables = page.extract_tables() or []
                    cleaned_tables: list[list[list[str]]] = []

                    for table in page_tables:
                        if not table:
                            continue

                        cleaned_rows: list[list[str]] = []
                        for row in table:
                            if not row:
                                continue

                            cleaned_row = [
                                re.sub(r"\s+", " ", str(cell).strip()) if cell is not None else ""
                                for cell in row
                            ]

                            if any(cell for cell in cleaned_row):
                                cleaned_rows.append(cleaned_row)

                        if cleaned_rows:
                            cleaned_tables.append(cleaned_rows)

                    if cleaned_tables:
                        extracted.extend(cleaned_tables)
        except Exception:
            return []

        return extracted

    def _extract_qr_payload_from_pdf(self, file_bytes: bytes) -> dict | str | None:
        try:
            doc = fitz.open(stream=file_bytes, filetype="pdf")
        except Exception:
            return None

        try:
            for page_index in range(len(doc)):
                page = doc.load_page(page_index)
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)

                img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(
                    pix.height,
                    pix.width,
                    pix.n,
                )

                if pix.n == 4:
                    img = cv2.cvtColor(img, cv2.COLOR_RGBA2BGR)
                elif pix.n == 3:
                    img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                decoded = decode_qr(gray)

                if not decoded:
                    thresholded = cv2.threshold(
                        gray,
                        0,
                        255,
                        cv2.THRESH_BINARY + cv2.THRESH_OTSU,
                    )[1]
                    decoded = decode_qr(thresholded)

                for qr in decoded:
                    raw = qr.data.decode("utf-8", errors="ignore").strip()
                    if not raw:
                        continue

                    try:
                        return json.loads(raw)
                    except Exception:
                        return raw
        except Exception:
            return None
        finally:
            doc.close()

        return None

    def _parse_invoice_header(
        self,
        raw_text: str,
        qr_payload: dict | str | None,
        is_purchase: bool,
    ) -> dict:
        normalized_text = raw_text or ""

        result = {
            "supplier_name": None,
            "supplier_tax_id": None,
            "client_name": None,
            "client_tax_id": None,
            "invoice_number": None,
            "invoice_date": None,
            "total_amount": None,
        }

        result["supplier_name"] = self._extract_invoice_supplier_name(normalized_text)
        result["client_name"] = self._extract_invoice_client_name(normalized_text)

        result["invoice_number"] = self._extract_invoice_number(normalized_text)
        result["invoice_date"] = self._extract_invoice_date(normalized_text)

        text_total = self._extract_total_amount(normalized_text)
        qr_total = self._extract_total_amount_from_qr(qr_payload)
        result["total_amount"] = qr_total or text_total

        result["supplier_tax_id"] = self._extract_first_cuit(normalized_text)
        result["client_tax_id"] = self._extract_second_cuit(normalized_text)

        if isinstance(qr_payload, dict):
            result["invoice_number"] = result["invoice_number"] or self._build_invoice_number_from_qr(qr_payload)
            result["invoice_date"] = result["invoice_date"] or self._parse_qr_date(qr_payload.get("fecha"))
            result["supplier_tax_id"] = result["supplier_tax_id"] or self._normalize_tax_id(self._safe_str(qr_payload.get("cuit")))

        return result
    
    async def commit_purchase_file(
        self,
        file: UploadFile,
        current_user: SalesRep | None,
        supplier_id: int | None = None,
        notes: str | None = None,
    ):
        self._validate_file_type(file)

        file_bytes = await file.read()
        raw_text = self._extract_text_from_pdf(file_bytes)
        extracted_tables = self._extract_tables_from_pdf(file_bytes)
        qr_payload = self._extract_qr_payload_from_pdf(file_bytes)

        header_data = self._parse_invoice_header(raw_text, qr_payload, is_purchase=True)
        items = self._parse_purchase_items(extracted_tables, raw_text)

        if not raw_text.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se pudo extraer texto del PDF",
            )

        if not items:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "No se pudieron detectar items de compra de forma confiable. "
                    "Usa preview-file + commit manual o corrige el parser."
                ),
            )

        commit_items: list[InvoiceItemCommit] = []

        for item in items:
            commit_items.append(
                InvoiceItemCommit(
                    product_id=None,
                    product_name=item.product_name,
                    product_sku=None,
                    quantity=item.quantity or 0,
                    unit_cost=item.unit_cost,
                    unit_price=item.unit_price,
                    is_user_edited=False,
                )
            )

        resolved_supplier_name = (header_data.get("supplier_name") or "").strip() or "Proveedor desconocido"
        resolved_supplier_tax_id = (header_data.get("supplier_tax_id") or "").strip() or None

        if supplier_id is not None:
            supplier = self.supplier_repo.get_by_id(supplier_id)
            if not supplier:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Proveedor no encontrado",
                )
            resolved_supplier_name = supplier.name
            resolved_supplier_tax_id = supplier.tax_id

        commit_data = PurchaseInvoiceImportCommitRequest(
            supplier_name=resolved_supplier_name,
            supplier_tax_id=resolved_supplier_tax_id,
            invoice_number=(header_data.get("invoice_number") or "").strip(),
            invoice_date=header_data.get("invoice_date"),
            notes=(notes or "").strip() or None,
            items=commit_items,
        )

        if not commit_data.invoice_number:
            # remitos sin número estándar AFIP: generar un identificador provisional
            commit_data.invoice_number = f"IMP-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        if not commit_data.invoice_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se pudo detectar la fecha del remito",
            )

        return self.commit_purchase(commit_data, current_user)

    async def commit_sales_file(
        self,
        file: UploadFile,
        current_user: SalesRep,
        client_id: int | None = None,
        client_branch_id: int | None = None,
        notes: str | None = None,
    ):
        self._validate_file_type(file)

        file_bytes = await file.read()
        raw_text = self._extract_text_from_pdf(file_bytes)
        extracted_tables = self._extract_tables_from_pdf(file_bytes)
        qr_payload = self._extract_qr_payload_from_pdf(file_bytes)

        header_data = self._parse_invoice_header(raw_text, qr_payload, is_purchase=False)
        items = self._parse_sales_items(extracted_tables, raw_text)

        if not raw_text.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se pudo extraer texto del PDF",
            )

        if not items:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "No se pudieron detectar items de venta de forma confiable. "
                    "Usa preview-file + commit manual o corrige el parser."
                ),
            )

        resolved_client_id = client_id
        detected_client_tax_id = (header_data.get("client_tax_id") or "").strip() or None

        if resolved_client_id is None and detected_client_tax_id:
            matched_client = self.client_repo.get_by_tax_id(detected_client_tax_id)
            if matched_client:
                resolved_client_id = matched_client.id

        if resolved_client_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "No se pudo resolver el cliente automáticamente. "
                    "Envía client_id o usa preview-file + commit manual."
                ),
            )

        commit_items: list[InvoiceItemCommit] = []

        for item in items:
            matched_product = None
            if item.product_name:
                matched_product = self.product_repo.get_product_by_name(item.product_name)

            commit_items.append(
                InvoiceItemCommit(
                    product_id=matched_product.id if matched_product else None,
                    product_name=item.product_name,
                    product_sku=None,
                    quantity=item.quantity or 0,
                    unit_cost=item.unit_cost,
                    unit_price=item.unit_price,
                    is_user_edited=False,
                )
            )

        unresolved_items = [item.product_name or "sin identificar" for item in commit_items if item.product_id is None]
        if unresolved_items:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "No se pudieron vincular automáticamente estos productos de venta: "
                    + ", ".join(unresolved_items)
                    + ". Usa preview-file + commit manual."
                ),
            )

        commit_data = SalesInvoiceImportCommitRequest(
            client_id=resolved_client_id,
            client_branch_id=client_branch_id,
            client_name=(header_data.get("client_name") or "").strip() or None,
            client_tax_id=detected_client_tax_id,
            invoice_number=(header_data.get("invoice_number") or "").strip(),
            invoice_date=header_data.get("invoice_date"),
            notes=(notes or "").strip() or None,
            items=commit_items,
        )

        if not commit_data.invoice_number:
            # remitos sin número estándar AFIP: generar un identificador provisional
            commit_data.invoice_number = f"IMP-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        if not commit_data.invoice_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se pudo detectar la fecha del remito",
            )

        return self.commit_sales(commit_data, current_user)

    def _extract_invoice_supplier_name(self, text: str) -> str | None:
        block = self._extract_block_between_markers(
            text,
            start_markers=["Proveedor / Emisor", "Emisor / Vendedor", "Proveedor", "Emisor"],
            end_markers=["Comprador / Receptor", "Cliente / Receptor", "Cliente", "Receptor"],
        )
        if block:
            labeled = self._extract_labeled_value(block, ["Razón Social", "Razon Social"])
            if labeled:
                return labeled

        return self._extract_first_razon_social(text) or self._extract_name_from_plain_header(text, position=0)

    def _extract_invoice_client_name(self, text: str) -> str | None:
        matches = self._extract_razon_social_values(text)
        if len(matches) > 1:
            return matches[1]

        block = self._extract_block_between_markers(
            text,
            start_markers=["Comprador / Receptor", "Cliente / Receptor"],
            end_markers=["Datos del comprobante", "Tipo", "Punto de Venta", "Comp. Nro"],
        )

        if block:
            block_matches = self._extract_razon_social_values(block)
            if len(block_matches) > 1:
                return block_matches[1]
            if len(block_matches) == 1:
                return block_matches[0]

        # fallback para remitos sin labels: primera línea de texto tras la fecha
        return self._extract_name_from_plain_header(text, position=0)
    
    def _extract_first_cuit(self, text: str) -> str | None:
        matches = self._extract_tax_ids(text)
        return matches[0] if matches else None

    def _extract_second_cuit(self, text: str) -> str | None:
        matches = self._extract_tax_ids(text)
        return matches[1] if len(matches) > 1 else None

    def _extract_block_between_markers(
        self,
        text: str,
        start_markers: list[str],
        end_markers: list[str],
    ) -> str | None:
        for start in start_markers:
            start_match = re.search(re.escape(start), text, re.IGNORECASE)
            if not start_match:
                continue

            start_idx = start_match.end()
            end_idx = len(text)

            for end in end_markers:
                end_match = re.search(re.escape(end), text[start_idx:], re.IGNORECASE)
                if end_match:
                    candidate_end = start_idx + end_match.start()
                    if candidate_end < end_idx:
                        end_idx = candidate_end

            block = text[start_idx:end_idx].strip()
            if block:
                return block

        return None

    def _extract_labeled_value(self, text: str, labels: list[str]) -> str | None:
        for label in labels:
            pattern = rf"{re.escape(label)}\s*:\s*([^\n\r]+)"
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                value = re.sub(r"\s+", " ", match.group(1)).strip()
                if value:
                    return value
        return None

    def _extract_razon_social_values(self, text: str) -> list[str]:
        matches = re.findall(
            r"Raz[oó]n Social\s*:\s*(.+?)(?=\s+Raz[oó]n Social\s*:|\s+CUIT\s*:|\s+IVA\s*:|\s+Domicilio\s*:|$)",
            text,
            flags=re.IGNORECASE | re.DOTALL,
        )

        cleaned: list[str] = []
        for value in matches:
            normalized = re.sub(r"\s+", " ", value).strip(" :.-")
            if normalized:
                cleaned.append(normalized)

        return cleaned

    def _extract_first_razon_social(self, text: str) -> str | None:
        matches = self._extract_razon_social_values(text)
        return matches[0] if matches else None

    def _extract_second_razon_social(self, text: str) -> str | None:
        matches = self._extract_razon_social_values(text)
        return matches[1] if len(matches) > 1 else None

    def _extract_name_from_plain_header(self, text: str, position: int = 0) -> str | None:
        """
        Para remitos sin labels AFIP (ej. remitos o tickets propios).
        Extrae nombres de persona/empresa de las primeras líneas del texto,
        saltando fechas, palabras clave de pago y líneas que empiezan con número.
        position=0 devuelve el primer nombre encontrado, position=1 el segundo, etc.
        """
        plain_header_blacklist = {
            "consumidor final",
            "cuenta corriente",
            "efectivo",
            "tarjeta",
            "cheque",
            "transferencia",
            "cuit",
            "iva",
            "remito",
            "presupuesto",
            "nota de credito",
            "nota de débito",
        }

        lines = [l.strip() for l in text.splitlines() if l.strip()]
        found: list[str] = []

        for line in lines[:20]:  # revisar solo el encabezado (primeras 20 líneas)
            # saltar fechas
            if re.match(r"^\d{1,2}/\d{1,2}/\d{4}$", line):
                continue
            # saltar líneas que empiezan con número seguido de espacio (ítems)
            if re.match(r"^\d+\s+[A-Z]", line):
                break  # los ítems ya comenzaron, no hay más encabezado
            # saltar totales y líneas solo numéricas
            if re.match(r"^[\$\d\.\,\s]+$", line):
                continue
            # saltar si contiene palabras clave de la blacklist
            lower = line.lower()
            if any(kw in lower for kw in plain_header_blacklist):
                continue
            # saltar líneas muy cortas
            if len(line) < 3:
                continue

            found.append(line)

        return found[position] if position < len(found) else None

    def _extract_tax_ids(self, text: str) -> list[str]:
        matches = re.findall(r"(?:(?:CUIT|Cuit)\s*:\s*)?((?:20|23|24|27|30|33|34)[\-\s]?\d{8}[\-\s]?\d)", text)
        normalized: list[str] = []

        for value in matches:
            cleaned = self._normalize_tax_id(value)
            if cleaned and cleaned not in normalized:
                normalized.append(cleaned)

        return normalized

    def _normalize_tax_id(self, value: str | None) -> str | None:
        if not value:
            return None
        digits = re.sub(r"\D", "", value)
        return digits or None

    def _map_qr_invoice_type(self, value) -> str | None:
        if value is None:
            return None

        mapping = {
            1: "A",
            6: "B",
            11: "C",
            51: "M",
        }

        try:
            numeric = int(value)
            return mapping.get(numeric)
        except Exception:
            return None

    def _parse_purchase_items(
        self,
        extracted_tables: list[list[list[str]]],
        raw_text: str,
    ) -> list[ParsedInvoiceItem]:
        items = self._parse_items_from_tables(extracted_tables, is_purchase=True)
        if items:
            return items
        return self._parse_items_from_text_lines(raw_text, is_purchase=True)

    def _parse_sales_items(
        self,
        extracted_tables: list[list[list[str]]],
        raw_text: str,
    ) -> list[ParsedInvoiceItem]:
        items = self._parse_items_from_tables(extracted_tables, is_purchase=False)
        if items:
            return items
        return self._parse_items_from_text_lines(raw_text, is_purchase=False)

    def _parse_items_from_tables(
        self,
        extracted_tables: list[list[list[str]]],
        is_purchase: bool,
    ) -> list[ParsedInvoiceItem]:
        parsed_items: list[ParsedInvoiceItem] = []

        for table in extracted_tables:
            for row in table:
                row_text = " ".join(cell for cell in row if cell).strip()
                if not row_text:
                    continue

                normalized_row = row_text.lower()

                if any(
                    token in normalized_row
                    for token in [
                        "cant.",
                        "detalle",
                        "p. unitario",
                        "subtotal",
                        "datos del comprobante",
                        "observaciones",
                        "iva",
                        "total",
                    ]
                ):
                    continue

                item = self._parse_item_from_row_text(row_text, is_purchase=is_purchase)
                if item:
                    parsed_items.append(item)

        return parsed_items

    def _parse_items_from_text_lines(
        self,
        raw_text: str,
        is_purchase: bool,
    ) -> list[ParsedInvoiceItem]:
        items: list[ParsedInvoiceItem] = []

        lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
        if not lines:
            return items

        for line in lines:
            normalized = line.lower()

            if any(
                token in normalized
                for token in [
                    "observaciones",
                    "qr afip",
                    "datos del comprobante",
                    "payload",
                    "subtotal",
                    "total",
                    "iva 21%",
                    "documento de prueba",
                ]
            ):
                continue

            item = self._parse_item_from_row_text(line, is_purchase=is_purchase)
            if item:
                items.append(item)

        return items

    def _parse_item_from_row_text(
        self,
        row_text: str,
        is_purchase: bool,
    ) -> ParsedInvoiceItem | None:

        compact = re.sub(r"\s+", " ", row_text).strip()

        if not compact:
            return None

        if len(compact) < 10:
            return None

        normalized = compact.lower()

        blacklist = [
            "subtotal",
            "total",
            "iva",
            "observaciones",
            "consumidor final",
            "cuenta corriente",
            "efectivo",
            "documento de prueba",
        ]

        if any(word in normalized for word in blacklist):
            return None

        # detecta montos tipo:
        # 1.275,0000  (precio unitario con 4 decimales, formato remito propio)
        # 12.750,00   (subtotal con 2 decimales)
        # 0,00        (columna de descuento, puede valer cero)
        money_matches = re.findall(
            r"\d[\d\.]*[\.,]\d+",
            compact,
        )

        if len(money_matches) < 2:
            return None

        try:

            # cantidad inicial (entero al comienzo de la línea)
            qty_match = re.match(
                r"^(\d+(?:[\.,]\d+)?)",
                compact,
            )

            if not qty_match:
                return None

            quantity_raw = qty_match.group(1)

            quantity_decimal = self._safe_decimal_from_arg_number(quantity_raw)

            if quantity_decimal is None:
                return None

            if quantity_decimal != quantity_decimal.to_integral_value():
                return None

            quantity = int(quantity_decimal)

            if quantity <= 0:
                return None

            # Estrategia de extracción de precio unitario y subtotal:
            #
            # Formato con descuento (remitos propios):
            #   qty  NOMBRE  precio_unit  descuento(0,00)  subtotal
            #   ej: "10 MILL - ESPERT 1.275,0000 0,00 12.750,00"
            #   → subtotal = último número, precio_unit = primer número > 0 desde
            #     el anteúltimo hacia atrás (saltamos ceros de descuento)
            #
            # Formato estándar AFIP:
            #   qty  NOMBRE  precio_unit  subtotal
            #   → mismo algoritmo funciona correctamente

            subtotal_raw = money_matches[-1]
            subtotal = self._safe_decimal_from_arg_number(subtotal_raw)

            unit_value = None
            for candidate_raw in reversed(money_matches[:-1]):
                candidate = self._safe_decimal_from_arg_number(candidate_raw)
                if candidate is not None and candidate > 0:
                    unit_value = candidate
                    break

            if subtotal is None or unit_value is None:
                return None

            # Validación cruzada: qty * precio_unit ≈ subtotal (tolerancia 5%)
            # Descarta líneas que no sean ítems reales (totales, encabezados, etc.)
            ratio = Decimal("0")
            if subtotal > 0 and unit_value > 0:
                expected = unit_value * quantity
                ratio = abs(expected - subtotal) / subtotal
                if ratio > Decimal("0.05"):
                    return None

            product_name = compact

            # remover la cantidad al inicio
            product_name = re.sub(
                r"^\d+(?:[\.,]\d+)?\s+",
                "",
                product_name,
            )

            # remover los montos numéricos del final por posición (más robusto que replace)
            # así evitamos borrar números que aparezcan dentro del nombre del producto
            name_tokens = product_name.split()
            tail_count = 0
            for token in reversed(name_tokens):
                if re.fullmatch(r"[\d\.\,]+", token):
                    tail_count += 1
                else:
                    break
            if tail_count:
                name_tokens = name_tokens[:-tail_count]
            # strip espacios y guiones sueltos al borde, preservando guiones en medio del nombre
            product_name = " ".join(name_tokens).strip().strip("-").strip()

            if len(product_name) < 3:
                return None

            # --- Confidence dinámico ---
            # Base: 0.5. Se suman puntos por cada señal positiva.
            confidence = Decimal("0.5")

            # Validación cruzada perfecta o casi perfecta
            if ratio == 0:
                confidence += Decimal("0.3")
            elif ratio <= Decimal("0.01"):
                confidence += Decimal("0.25")
            elif ratio <= Decimal("0.03"):
                confidence += Decimal("0.15")
            else:
                confidence += Decimal("0.05")

            # Nombre de producto razonable (más de 3 palabras y sin caracteres raros)
            word_count = len(product_name.split())
            if word_count >= 2:
                confidence += Decimal("0.1")
            if word_count >= 4:
                confidence += Decimal("0.05")
            if re.search(r"[^\w\s\-\./&°ÁÉÍÓÚáéíóúÑñ]", product_name):
                confidence -= Decimal("0.1")  # caracteres extraños = parsing dudoso

            # Cantidad razonable (entre 1 y 9999)
            if 1 <= quantity <= 9999:
                confidence += Decimal("0.05")

            confidence = max(Decimal("0.0"), min(Decimal("1.0"), confidence))

            return ParsedInvoiceItem(
                product_name=product_name,
                quantity=quantity,
                unit_cost=unit_value if is_purchase else None,
                unit_price=None if is_purchase else unit_value,
                subtotal=subtotal,
                confidence=float(round(confidence, 2)),
                warnings=[],
            )

        except Exception:
            return None

    def _safe_int(self, value: str | None) -> int | None:
        if value is None:
            return None
        try:
            return int(str(value).strip())
        except Exception:
            return None

    def _extract_invoice_type(self, text: str) -> str | None:
        match = re.search(r"\bREMITO\s+([ABCEM])\b", text, re.IGNORECASE)
        if match:
            return match.group(1).upper()

        match = re.search(r"\bRemito\s+([ABCEM])\b", text, re.IGNORECASE)
        if match:
            return match.group(1).upper()

        match = re.search(r"\bTipo\s*:\s*REMITO\s+([ABCEM])\b", text, re.IGNORECASE)
        if match:
            return match.group(1).upper()

        return None

    def _extract_invoice_number(self, text: str) -> str | None:
        patterns = [
            r"(?:Punto de Venta|Pto\.?\s*Vta\.?|Punto Venta)\s*[:\-]?\s*(\d{4}).{0,30}?(?:Comp\.?\s*Nro|Comprobante\s*N[°º]?|Comp Nro)\s*[:\-]?\s*(\d{8})",
            r"\b(\d{4})-(\d{8})\b",
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                return f"{match.group(1)}-{match.group(2)}"

        return None

    def _extract_invoice_date(self, text: str) -> date | None:
        patterns = [
            r"(?:Fecha de Emisi[oó]n|Fecha)\s*[:\-]?\s*(\d{1,2}/\d{1,2}/\d{4})",
            r"\b(\d{4}-\d{2}-\d{2})\b",
            # fecha sola al inicio de línea sin label (ej. "11/5/2026" o "10/4/2026")
            r"(?:^|\n)\s*(\d{1,2}/\d{1,2}/\d{4})\s*(?:\n|$)",
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if not match:
                continue

            parsed = self._parse_date(match.group(1))
            if parsed:
                return parsed

        return None

    def _extract_total_amount(self, text: str) -> Decimal | None:
        patterns = [
            r"(?:Importe Total|Total)\s*[:\-]?\s*\$?\s*([\d\.\,]+)",
            r"Total\s+\$?\s*([\d\.\,]+)",
        ]

        matches: list[Decimal] = []

        for pattern in patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                value = self._safe_decimal_from_arg_number(match.group(1))
                if value is not None:
                    matches.append(value)

        if matches:
            return matches[-1]

        # fallback: buscar un número precedido por $ al final del texto
        # (remitos propios que imprimen el total como "$ 66.100,00" sin label)
        dollar_matches = re.findall(r"\$\s*([\d\.\,]+)", text)
        for raw in reversed(dollar_matches):
            value = self._safe_decimal_from_arg_number(raw)
            if value and value > 0:
                return value

        return None

    def _extract_total_amount_from_qr(self, qr_payload: dict | str | None) -> Decimal | None:
        if not isinstance(qr_payload, dict):
            return None
        return self._safe_decimal(qr_payload.get("importe"))

    def _build_invoice_number_from_qr(self, qr_payload: dict) -> str | None:
        pto_vta = qr_payload.get("ptoVta")
        nro_cmp = qr_payload.get("nroCmp")

        if pto_vta is None or nro_cmp is None:
            return None

        try:
            return f"{int(pto_vta):04d}-{int(nro_cmp):08d}"
        except Exception:
            return None

    def _parse_qr_date(self, value) -> date | None:
        if value is None:
            return None
        return self._parse_date(str(value))

    def _parse_date(self, value: str) -> date | None:
        for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%-d/%-m/%Y"):
            try:
                return datetime.strptime(value.strip(), fmt).date()
            except ValueError:
                continue
        # fallback manual para D/M/YYYY o DD/M/YYYY sin padding
        try:
            parts = value.strip().split("/")
            if len(parts) == 3:
                day, month, year = int(parts[0]), int(parts[1]), int(parts[2])
                return date(year, month, day)
        except Exception:
            pass
        return None

    def _safe_decimal(self, value) -> Decimal | None:
        if value is None:
            return None
        try:
            return Decimal(str(value))
        except Exception:
            return None

    def _safe_decimal_from_arg_number(self, value: str) -> Decimal | None:
        if not value:
            return None

        cleaned = value.strip().replace(" ", "").replace("$", "")

        if "," in cleaned and "." in cleaned:
            cleaned = cleaned.replace(".", "").replace(",", ".")
        elif "," in cleaned:
            cleaned = cleaned.replace(",", ".")

        try:
            return Decimal(cleaned)
        except Exception:
            return None

    def _safe_str(self, value) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        return text or None