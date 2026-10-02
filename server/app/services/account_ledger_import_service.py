import io
import uuid
from collections import defaultdict
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

import pandas as pd
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.constants.account_movement_constant import ALLOWED_PAYMENT_METHODS
from app.constants.sales_type_constant import SalesType
from app.repositories.client_repository import ClientRepository
from app.repositories.product_repository import ProductRepository
from app.repositories.sales_invoice_repository import SalesInvoiceRepository
from app.repositories.sales_quote_repository import SalesQuoteRepository
from app.repositories.sales_rep_repository import SalesRepRepository
from app.repositories.supplier_repository import SupplierRepository
from app.schemas.account_ledger_import_schema import (
    ClientImportPaymentResult,
    ClientImportResult,
    ClientImportRow,
    ClientImportRowError,
    SupplierImportResult,
    SupplierImportRow,
    SupplierImportRowError,
)
from app.schemas.account_movement_schema import (
    ClientPaymentCreate,
    ClientPaymentAllocationItem,
)
from app.schemas.purchase_invoice_schema import (
    PurchaseInvoiceCreate,
    PurchaseInvoiceItemCreate,
)
from app.schemas.purchase_quote_schema import (
    PurchaseQuoteCreate,
    PurchaseQuoteItemCreate,
)
from app.schemas.sales_invoice_schema import (
    ClientSnapshot,
    SalesInvoiceCreate,
    SalesInvoiceItemCreate,
    SalesRepSnapshot,
)
from app.schemas.sales_quote_schema import (
    SalesQuoteCreate,
    SalesQuoteItemCreate,
)
from app.services.account_ledger_service import AccountLedgerService
from app.services.client_account_movement_service import (
    ClientAccountMovementService,
)
from app.services.purchase_invoice_service import PurchaseInvoiceService
from app.services.purchase_quote_service import PurchaseQuoteService
from app.services.sales_invoice_service import SalesInvoiceService
from app.services.sales_quote_service import SalesQuoteService
from app.models.sales_invoice_model import SalesInvoice
from app.models.sales_quote_model import SalesQuote
from app.utils.import_matching import row_signature

ZERO = Decimal("0.00")


# ======================================================================
# Columnas de hojas de vendedores
# ======================================================================

_PRODUCT_COL_HINTS = [
    "pedido",
    "producto",
    "articulo",
    "artículo",
]

_QUANTITY_COL_HINTS = [
    "cantidad a comprar",
    "cantidad",
    "cant.",
    "cant",
]

_COST_COL_HINTS = [
    "costo",
]

_UNIT_PRICE_COL_HINTS = [
    "precio unitario",
    "precio venta",
    "precio",
    "valor unitario",
    "importe unitario",
]

_CLIENT_NAME_HINTS = [
    "cliente",
    "clientes",
    "nombre cliente",
]


# ======================================================================
# Columnas de REGISTRO CLIENTES
# ======================================================================

_CLIENT_DATE_HINTS = [
    "fecha",
]

_CLIENT_STATUS_HINTS = [
    "estado",
]

_CLIENT_AMOUNT_HINTS = [
    "importe",
    "total",
    "monto",
]

_CLIENT_PAYMENT_METHOD_HINTS = [
    "forma de pago",
    "método de pago",
    "metodo de pago",
]

_CLIENT_SALES_REP_HINTS = [
    "vendedor",
    "vendedora",
]


# ======================================================================
# Columna "document": remito (invoice) o presupuesto (quote), por fila
# ======================================================================

_DOCUMENT_COL_HINTS = [
    "document",
]

_DOCUMENT_INVOICE_VALUES = {"invoice", "remito", "remitos"}
_DOCUMENT_QUOTE_VALUES = {"quote", "presupuesto", "presupuestos", "cotizacion"}


# ======================================================================
# Hojas que no son vendedores
# ======================================================================

_NON_SALES_REP_SHEET_HINTS = [
    "registro clientes",
    "registro de clientes",
    "listado de productos",
    "lista de productos",
    "balance stock",
    "balance de stock",
    "calendario",
    "caja",
]


# ======================================================================
# Métodos de pago
# ======================================================================

_CLIENT_METHOD_AMOUNT_COLUMNS: list[tuple[str, str]] = [
    ("efectivo", "efectivo"),
    ("transferencia", "otro"),
    ("cheque", "cheque"),
    ("depósito", "otro"),
    ("deposito", "otro"),
]

_PAYMENT_METHOD_TEXT_MAP = {
    "efectivo": "efectivo",
    "cheque": "cheque",
    "credito": "credito",
    "crédito": "credito",
    "debito": "debito",
    "débito": "debito",
    "transferencia": "otro",
    "depósito": "otro",
    "deposito": "otro",
}


# ======================================================================
# Helpers generales
# ======================================================================

def _normalize_name(value: str | None) -> str:
    if value is None:
        return ""

    text = str(value).strip().lower()

    replacements = str.maketrans(
        {
            "á": "a",
            "é": "e",
            "í": "i",
            "ó": "o",
            "ú": "u",
            "ü": "u",
            "ñ": "n",
        }
    )

    text = text.translate(replacements)

    return " ".join(text.split())


def _normalize_column(value) -> str:
    return _normalize_name(str(value))


def _find_column(columns: list, hints: list[str]) -> str | None:
    """
    Busca una columna usando coincidencia normalizada.

    Ejemplos:
        "Cantidad a comprar" coincide con "cantidad"
        "PRECIO UNITARIO" coincide con "precio"
    """
    normalized_columns = {
        column: _normalize_column(column)
        for column in columns
    }

    normalized_hints = [
        _normalize_name(hint)
        for hint in hints
    ]

    for hint in normalized_hints:
        for column, normalized_column in normalized_columns.items():
            if hint in normalized_column:
                return column

    return None


def _is_empty(value) -> bool:
    if value is None:
        return True

    try:
        if pd.isna(value):
            return True
    except (TypeError, ValueError):
        pass

    if isinstance(value, str) and not value.strip():
        return True

    return False


def _to_decimal(value) -> Decimal | None:
    if _is_empty(value):
        return None

    try:
        text = str(value).strip()

        text = text.replace("$", "")
        text = text.replace(" ", "")

        # Formato argentino:
        # 1.500,50 -> 1500.50
        if "," in text and "." in text:
            if text.rfind(",") > text.rfind("."):
                text = text.replace(".", "").replace(",", ".")
            else:
                text = text.replace(",", "")
        elif "," in text:
            text = text.replace(",", ".")

        return Decimal(text)

    except (
        InvalidOperation,
        ValueError,
        TypeError,
    ):
        return None


def _parse_excel_date(value) -> date | None:
    if _is_empty(value):
        return None

    if isinstance(value, datetime):
        return value.date()

    if isinstance(value, date):
        return value

    parsed = pd.to_datetime(
        value,
        errors="coerce",
        dayfirst=True,
    )

    if pd.isna(parsed):
        return None

    return parsed.date()


def _parse_document_kind(raw) -> str | None:
    """
    Interpreta la celda de la columna "document".

    Devuelve "invoice" (remito), "quote" (presupuesto) o None si la celda
    está vacía (en ese caso se usa el tipo por defecto del import).
    Lanza ValueError con un mensaje listo para mostrar si el valor no se
    reconoce, para no crear un documento del tipo equivocado en silencio.
    """
    if _is_empty(raw):
        return None

    normalized = _normalize_name(raw)

    if normalized in _DOCUMENT_INVOICE_VALUES:
        return "invoice"

    if normalized in _DOCUMENT_QUOTE_VALUES:
        return "quote"

    raise ValueError(
        f"Valor '{str(raw).strip()}' inválido en la columna 'document' "
        "(usar remito/invoice o presupuesto/quote)"
    )


def _map_payment_method(raw: str | None) -> str:
    if not raw:
        return "otro"

    normalized = _normalize_name(raw)

    return _PAYMENT_METHOD_TEXT_MAP.get(
        normalized,
        "otro",
    )


def _generate_invoice_number(prefix: str) -> str:
    safe_prefix = (
        _normalize_name(prefix)
        .replace(" ", "")
        .upper()[:10]
    )

    return (
        f"IMP-{safe_prefix}-"
        f"{datetime.now().strftime('%Y%m%d%H%M%S')}-"
        f"{uuid.uuid4().hex[:6]}"
    )


# ======================================================================
# Service
# ======================================================================

class AccountLedgerImportService:
    def __init__(self, db: Session):
        self.db = db

        self.client_repo = ClientRepository(db)
        self.supplier_repo = SupplierRepository(db)
        self.sales_rep_repo = SalesRepRepository(db)
        self.product_repo = ProductRepository(db)
        self.sales_invoice_repo = SalesInvoiceRepository(db)
        self.sales_quote_repo = SalesQuoteRepository(db)

        self.purchase_invoice_service = PurchaseInvoiceService(db)
        self.purchase_quote_service = PurchaseQuoteService(db)
        self.sales_invoice_service = SalesInvoiceService(db)
        self.sales_quote_service = SalesQuoteService(db)

        self.client_account_movement_service = (
            ClientAccountMovementService(db)
        )

        self.ledger_service = AccountLedgerService(db)

    # ==================================================================
    # Proveedores
    # ==================================================================

    def import_supplier_purchases(
        self,
        *,
        file_bytes: bytes,
        sheet_name: str | None,
        sales_rep_id: int,
        supplier_id: int,
        purchase_date: date,
        document_type: str = "purchase_invoice",
        dry_run: bool,
        current_user,
    ) -> SupplierImportResult:

        sales_rep = self.sales_rep_repo.get_by_id(sales_rep_id)

        if not sales_rep:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND,
                "Vendedor no encontrado",
            )

        supplier = self.supplier_repo.get_by_id(supplier_id)

        if not supplier:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND,
                "Proveedor no encontrado",
            )

        if document_type not in ("purchase_invoice", "purchase_quote"):
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                "document_type inválido (usar purchase_invoice o purchase_quote)",
            )

        try:
            excel = pd.ExcelFile(io.BytesIO(file_bytes))
        except Exception as exc:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                f"Error al leer el Excel: {exc}",
            )

        resolved_sheet = sheet_name or sales_rep.name

        matched_sheet = next(
            (
                sheet
                for sheet in excel.sheet_names
                if _normalize_name(sheet)
                == _normalize_name(resolved_sheet)
            ),
            None,
        )

        if not matched_sheet:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                (
                    f"No se encontró la hoja '{resolved_sheet}'. "
                    f"Hojas disponibles: {', '.join(excel.sheet_names)}"
                ),
            )

        df = pd.read_excel(
            excel,
            sheet_name=matched_sheet,
            header=0,
        )

        columns = list(df.columns)

        product_col = _find_column(
            columns,
            _PRODUCT_COL_HINTS,
        )

        quantity_col = _find_column(
            columns,
            _QUANTITY_COL_HINTS,
        )

        cost_col = _find_column(
            columns,
            _COST_COL_HINTS,
        )

        document_col = _find_column(
            columns,
            _DOCUMENT_COL_HINTS,
        )

        missing = [
            label
            for label, column in [
                ("producto", product_col),
                ("cantidad", quantity_col),
                ("costo", cost_col),
            ]
            if column is None
        ]

        if missing:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                (
                    "No se encontraron estas columnas en la hoja: "
                    f"{', '.join(missing)}"
                ),
            )

        rows_valid: list[SupplierImportRow] = []
        rows_invalid: list[SupplierImportRowError] = []

        for index, row in df.iterrows():
            row_number = index + 2

            quantity_raw = row.get(quantity_col)
            product_name_raw = row.get(product_col)

            if _is_empty(quantity_raw):
                continue

            errors: list[str] = []

            product_name = (
                str(product_name_raw).strip()
                if not _is_empty(product_name_raw)
                else ""
            )

            if not product_name:
                errors.append(
                    "Falta el nombre del producto"
                )

            quantity = _to_decimal(quantity_raw)

            if quantity is None or quantity <= 0:
                errors.append(
                    "Cantidad inválida"
                )

            cost = _to_decimal(
                row.get(cost_col)
            )

            if cost is None or cost <= 0:
                errors.append(
                    "Costo inválido o faltante"
                )

            # Columna "document": remito/invoice o presupuesto/quote.
            # Vacía (o sin columna) => tipo por defecto del import.
            row_document_type = document_type

            if document_col is not None:
                try:
                    document_kind = _parse_document_kind(
                        row.get(document_col)
                    )
                except ValueError as exc:
                    errors.append(str(exc))
                else:
                    if document_kind is not None:
                        row_document_type = f"purchase_{document_kind}"

            if errors:
                rows_invalid.append(
                    SupplierImportRowError(
                        row_number=row_number,
                        errors=errors,
                    )
                )
                continue

            rows_valid.append(
                SupplierImportRow(
                    row_number=row_number,
                    product_name=product_name,
                    quantity=int(quantity),
                    unit_cost=cost,
                    document_type=row_document_type,
                )
            )

        total_amount = sum(
            (
                row.unit_cost * row.quantity
                for row in rows_valid
            ),
            ZERO,
        )

        result = SupplierImportResult(
            dry_run=dry_run,
            sheet_name=matched_sheet,
            total_rows_read=len(df),
            rows_to_import=rows_valid,
            rows_with_errors=rows_invalid,
            total_amount=total_amount,
            document_type=document_type,
        )

        if dry_run or not rows_valid:
            return result

        # Un mismo Excel puede traer filas de remito y de presupuesto (columna
        # "document"): se crea un documento de cada tipo con sus filas.
        quote_rows = [
            row
            for row in rows_valid
            if row.document_type == "purchase_quote"
        ]
        invoice_rows = [
            row
            for row in rows_valid
            if row.document_type == "purchase_invoice"
        ]

        if quote_rows:
            # Un presupuesto de compra no afecta stock ni cuenta corriente
            # (igual que uno cargado a mano): solo deja constancia de la
            # cotización. No se confirma, no genera deuda con el proveedor.
            quote = self.purchase_quote_service.create(
                PurchaseQuoteCreate(
                    supplier_id=supplier.id,
                    supplier_name=supplier.name,
                    quote_number=_generate_invoice_number(
                        sales_rep.name
                    ),
                    quote_date=purchase_date,
                    notes=(
                        f"Importado desde Excel — hoja "
                        f"'{matched_sheet}'"
                    ),
                    items=[
                        PurchaseQuoteItemCreate(
                            product_name=row.product_name,
                            quantity=row.quantity,
                            unit_cost=row.unit_cost,
                        )
                        for row in quote_rows
                    ],
                ),
                current_user,
            )

            quote.created_by = sales_rep.id
            self.db.add(quote)
            self.db.flush()

            result.purchase_quote_id = quote.id

        if invoice_rows:
            purchase_invoice_data = PurchaseInvoiceCreate(
                supplier_id=supplier.id,
                supplier_name=supplier.name,
                invoice_number=_generate_invoice_number(
                    sales_rep.name
                ),
                invoice_date=purchase_date,
                notes=(
                    f"Importado desde Excel — hoja "
                    f"'{matched_sheet}'"
                ),
                items=[
                    PurchaseInvoiceItemCreate(
                        product_name=row.product_name,
                        quantity=row.quantity,
                        unit_cost=row.unit_cost,
                    )
                    for row in invoice_rows
                ],
            )

            invoice = self.purchase_invoice_service.create(
                purchase_invoice_data,
                current_user,
            )

            invoice.created_by = sales_rep.id

            self.db.add(invoice)
            self.db.flush()

            self.purchase_invoice_service.update_status(
                invoice.id,
                "confirmed",
                current_user,
            )

            self.db.flush()

            result.purchase_invoice_id = invoice.id

        return result

    # ==================================================================
    # Helpers de vendedores / productos / clientes
    # ==================================================================

    def _get_sales_rep_by_sheet_name(
        self,
        sheet_name: str,
    ):
        """
        Busca el vendedor cuyo nombre corresponde al nombre de la pestaña.

        Primero intenta el repository normal y luego compara nombres
        normalizados para soportar diferencias de mayúsculas y tildes.
        """
        sales_rep = self.sales_rep_repo.get_by_name(
            sheet_name
        )

        if sales_rep:
            return sales_rep

        # Fallback:
        # si el repository tiene un método para listar vendedores,
        # podés reemplazar este bloque por ese método.
        #
        # Intentamos buscar mediante la sesión para evitar depender
        # de una normalización distinta en get_by_name.
        from app.models.sales_rep_model import SalesRep

        candidates = (
            self.db.query(SalesRep)
            .filter(SalesRep.is_active.is_(True))
            .all()
        )

        normalized_sheet = _normalize_name(sheet_name)

        for candidate in candidates:
            if (
                _normalize_name(candidate.name)
                == normalized_sheet
            ):
                return candidate

        return None

    def _get_client_by_name(
        self,
        client_name: str,
    ):
        client = self.client_repo.get_by_name(
            client_name
        )

        if client:
            return client

        from app.models.client_model import Client

        normalized_name = _normalize_name(client_name)

        candidates = (
            self.db.query(Client)
            .filter(Client.is_active.is_(True))
            .all()
        )

        for candidate in candidates:
            if (
                _normalize_name(candidate.name)
                == normalized_name
            ):
                return candidate

        return None

    def _get_product_by_name(
        self,
        product_name: str,
    ):
        product = self.product_repo.get_product_by_name(
            product_name
        )

        if product:
            return product

        from app.models.product_model import Product

        normalized_name = _normalize_name(product_name)

        candidates = (
            self.db.query(Product)
            .all()
        )

        for candidate in candidates:
            if (
                _normalize_name(candidate.name)
                == normalized_name
            ):
                return candidate

        return None

    def _is_non_sales_rep_sheet(
        self,
        sheet_name: str,
        registry_sheet: str,
    ) -> bool:
        normalized_sheet = _normalize_name(sheet_name)

        if (
            normalized_sheet
            == _normalize_name(registry_sheet)
        ):
            return True

        return any(
            hint in normalized_sheet
            for hint in _NON_SALES_REP_SHEET_HINTS
        )

    # ==================================================================
    # Detectar columnas de una hoja de vendedor
    # ==================================================================

    def _resolve_sales_sheet_columns(
        self,
        df: pd.DataFrame,
    ) -> dict[str, str | None]:
        columns = list(df.columns)

        return {
            "client": _find_column(
                columns,
                _CLIENT_NAME_HINTS,
            ),
            "product": _find_column(
                columns,
                _PRODUCT_COL_HINTS,
            ),
            "quantity": _find_column(
                columns,
                _QUANTITY_COL_HINTS,
            ),
            "unit_price": _find_column(
                columns,
                _UNIT_PRICE_COL_HINTS,
            ),
            "document": _find_column(
                columns,
                _DOCUMENT_COL_HINTS,
            ),
        }

    # ==================================================================
    # Leer ventas de todas las pestañas de vendedores
    # ==================================================================

    def _parse_sales_rep_sheets(
        self,
        *,
        excel: pd.ExcelFile,
        registry_sheet: str,
        default_document_type: str = "sales_invoice",
    ) -> tuple[
        list[ClientImportRow],
        list[ClientImportRowError],
        list[dict],
    ]:
        """
        Lee TODAS las hojas de vendedores.

        Cada venta válida devuelve:
            - ClientImportRow: para preview
            - contexto interno: objetos reales Client/Product/SalesRep

        Una fila se considera una venta cuando contiene:
            cliente + producto + cantidad

        El precio se toma del Excel cuando existe una columna de precio.
        Si no existe, se utiliza product.unit_price.

        Si la hoja tiene una columna "document", cada fila indica si es un
        remito (invoice) o un presupuesto (quote). Las celdas vacías (o la
        ausencia de la columna) usan default_document_type.
        """

        rows_valid: list[ClientImportRow] = []
        rows_invalid: list[ClientImportRowError] = []
        creation_ctx: list[dict] = []

        for sheet_name in excel.sheet_names:

            if self._is_non_sales_rep_sheet(
                sheet_name,
                registry_sheet,
            ):
                continue

            # ----------------------------------------------------------
            # Primero verificamos que la pestaña sea realmente
            # un vendedor existente.
            # ----------------------------------------------------------

            sales_rep = self._get_sales_rep_by_sheet_name(
                sheet_name
            )

            if not sales_rep:
                # No agregamos error todavía si la hoja claramente no
                # contiene una estructura de ventas.
                try:
                    probe_df = pd.read_excel(
                        excel,
                        sheet_name=sheet_name,
                        header=0,
                    )
                except Exception:
                    continue

                probe_columns = self._resolve_sales_sheet_columns(
                    probe_df
                )

                has_sales_structure = (
                    probe_columns["client"] is not None
                    and probe_columns["product"] is not None
                    and probe_columns["quantity"] is not None
                )

                if has_sales_structure:
                    rows_invalid.append(
                        ClientImportRowError(
                            row_number=0,
                            errors=[
                                (
                                    f"Pestaña '{sheet_name}': "
                                    "no existe un vendedor con ese "
                                    "nombre en la base de datos"
                                )
                            ],
                        )
                    )

                continue

            # ----------------------------------------------------------
            # Leer hoja
            # ----------------------------------------------------------

            try:
                df = pd.read_excel(
                    excel,
                    sheet_name=sheet_name,
                    header=0,
                )
            except Exception as exc:
                rows_invalid.append(
                    ClientImportRowError(
                        row_number=0,
                        errors=[
                            (
                                f"No se pudo leer la pestaña "
                                f"'{sheet_name}': {exc}"
                            )
                        ],
                    )
                )
                continue

            resolved = self._resolve_sales_sheet_columns(
                df
            )

            client_col = resolved["client"]
            product_col = resolved["product"]
            quantity_col = resolved["quantity"]
            unit_price_col = resolved["unit_price"]
            document_col = resolved["document"]

            # Una hoja de vendedor puede tener otras secciones,
            # pero si no tiene estas 3 columnas no sirve para ventas.
            if (
                client_col is None
                or product_col is None
                or quantity_col is None
            ):
                continue

            # ----------------------------------------------------------
            # Recorrer filas
            # ----------------------------------------------------------

            for index, row in df.iterrows():
                row_number = index + 2

                raw_client = row.get(client_col)
                raw_product = row.get(product_col)
                raw_quantity = row.get(quantity_col)

                # Filas vacías / separadores.
                if (
                    _is_empty(raw_client)
                    and _is_empty(raw_product)
                    and _is_empty(raw_quantity)
                ):
                    continue

                errors: list[str] = []

                client_name = (
                    str(raw_client).strip()
                    if not _is_empty(raw_client)
                    else ""
                )

                product_name = (
                    str(raw_product).strip()
                    if not _is_empty(raw_product)
                    else ""
                )

                quantity = _to_decimal(
                    raw_quantity
                )

                # ------------------------------------------------------
                # Validaciones básicas
                # ------------------------------------------------------

                if not client_name:
                    errors.append(
                        "Falta el nombre del cliente"
                    )

                if not product_name:
                    errors.append(
                        "Falta el nombre del producto"
                    )

                if (
                    quantity is None
                    or quantity <= 0
                ):
                    errors.append(
                        "Cantidad inválida o faltante"
                    )

                # ------------------------------------------------------
                # Cliente
                # ------------------------------------------------------

                matched_client = None

                if client_name:
                    matched_client = (
                        self._get_client_by_name(
                            client_name
                        )
                    )

                    if not matched_client:
                        errors.append(
                            (
                                f"Cliente '{client_name}' no "
                                "encontrado en la base de datos"
                            )
                        )

                # ------------------------------------------------------
                # Producto
                # ------------------------------------------------------

                product = None

                if product_name:
                    product = self._get_product_by_name(
                        product_name
                    )

                    if not product:
                        errors.append(
                            (
                                f"Producto '{product_name}' no "
                                "encontrado en la base de datos"
                            )
                        )

                    elif not product.is_active:
                        errors.append(
                            (
                                f"El producto '{product_name}' "
                                "está inactivo"
                            )
                        )

                # ------------------------------------------------------
                # Precio
                # ------------------------------------------------------

                excel_unit_price = None

                if unit_price_col is not None:
                    excel_unit_price = _to_decimal(
                        row.get(unit_price_col)
                    )

                    if (
                        excel_unit_price is not None
                        and excel_unit_price <= 0
                    ):
                        errors.append(
                            "Precio unitario inválido"
                        )

                # ------------------------------------------------------
                # Tipo de documento (columna "document")
                # ------------------------------------------------------

                document_type = default_document_type

                if document_col is not None:
                    try:
                        document_kind = _parse_document_kind(
                            row.get(document_col)
                        )
                    except ValueError as exc:
                        errors.append(str(exc))
                    else:
                        if document_kind is not None:
                            document_type = f"sales_{document_kind}"

                if errors:
                    rows_invalid.append(
                        ClientImportRowError(
                            row_number=row_number,
                            errors=[
                                (
                                    f"[{sheet_name}] {error}"
                                )
                                for error in errors
                            ],
                        )
                    )
                    continue

                # ------------------------------------------------------
                # Precio final
                # ------------------------------------------------------

                if excel_unit_price is not None:
                    unit_price = excel_unit_price
                else:
                    unit_price = Decimal(
                        str(product.unit_price or 0)
                    )

                if unit_price <= 0:
                    rows_invalid.append(
                        ClientImportRowError(
                            row_number=row_number,
                            errors=[
                                (
                                    f"[{sheet_name}] El producto "
                                    f"'{product.name}' no tiene un "
                                    "precio de venta válido"
                                )
                            ],
                        )
                    )
                    continue

                total_amount = (
                    unit_price * quantity
                )

                # ------------------------------------------------------
                # La fecha de la factura se decide después.
                #
                # Usamos la fecha actual como valor temporal para el
                # schema existente.
                # ------------------------------------------------------

                sale_date = date.today()

                rows_valid.append(
                    ClientImportRow(
                        row_number=row_number,
                        client_name=client_name,
                        matched_client_id=matched_client.id,
                        product_name=product_name,
                        quantity=int(quantity),
                        sale_date=sale_date,
                        amount=total_amount,
                        payment_method_raw=None,
                        is_paid=False,
                        sales_rep_id=sales_rep.id,
                        sales_rep_name=sales_rep.name,
                        document_type=document_type,
                    )
                )

                creation_ctx.append(
                    {
                        "sheet_name": sheet_name,
                        "row_number": row_number,
                        "sales_rep": sales_rep,
                        "client": matched_client,
                        "product": product,
                        "quantity": quantity,
                        "unit_price": unit_price,
                        "sale_date": sale_date,
                        "document_type": document_type,
                    }
                )

        return (
            rows_valid,
            rows_invalid,
            creation_ctx,
        )

    # ==================================================================
    # Leer pagos desde REGISTRO CLIENTES
    # ==================================================================

    def _parse_client_registry(
        self,
        *,
        excel: pd.ExcelFile,
        registry_sheet: str,
    ) -> tuple[list[dict], list[ClientImportRowError]]:
        """
        REGISTRO CLIENTES NO genera facturas.

        Su función es representar movimientos de cuenta corriente,
        especialmente pagos/cobranzas.

        Las ventas salen exclusivamente de las pestañas de vendedores.
        """

        df = pd.read_excel(
            excel,
            sheet_name=registry_sheet,
            header=0,
        )

        columns = list(df.columns)

        date_col = _find_column(
            columns,
            _CLIENT_DATE_HINTS,
        )

        client_col = _find_column(
            columns,
            _CLIENT_NAME_HINTS,
        )

        status_col = _find_column(
            columns,
            _CLIENT_STATUS_HINTS,
        )

        amount_col = _find_column(
            columns,
            _CLIENT_AMOUNT_HINTS,
        )

        payment_method_col = _find_column(
            columns,
            _CLIENT_PAYMENT_METHOD_HINTS,
        )

        missing = [
            label
            for label, column in [
                ("cliente", client_col),
                ("importe", amount_col),
            ]
            if column is None
        ]

        if missing:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                (
                    "No se encontraron estas columnas en "
                    f"REGISTRO CLIENTES: {', '.join(missing)}"
                ),
            )

        # --------------------------------------------------------------
        # Forward-fill de fechas
        # --------------------------------------------------------------

        filled_dates: list[date | None] = []

        if date_col is not None:
            last_date: date | None = None

            for raw_date in df[date_col].tolist():
                parsed_date = _parse_excel_date(
                    raw_date
                )

                if parsed_date is not None:
                    last_date = parsed_date

                filled_dates.append(
                    last_date
                )
        else:
            filled_dates = [
                None
                for _ in range(len(df))
            ]

        payments: list[dict] = []
        errors: list[ClientImportRowError] = []

        # Detectamos una sola vez las columnas de métodos.
        method_columns: list[tuple[str, str]] = []

        for hint, mapped_method in (
            _CLIENT_METHOD_AMOUNT_COLUMNS
        ):
            actual_column = _find_column(
                columns,
                [hint],
            )

            if actual_column is not None:
                method_columns.append(
                    (
                        actual_column,
                        mapped_method,
                    )
                )

        for index, row in df.iterrows():
            row_number = index + 2

            raw_client = row.get(client_col)
            raw_amount = row.get(amount_col)

            if (
                _is_empty(raw_client)
                and _is_empty(raw_amount)
            ):
                continue

            row_errors: list[str] = []

            client_name = (
                str(raw_client).strip()
                if not _is_empty(raw_client)
                else ""
            )

            amount = _to_decimal(
                raw_amount
            )

            if not client_name:
                row_errors.append(
                    "Falta el nombre del cliente"
                )

            if (
                amount is None
                or amount <= 0
            ):
                row_errors.append(
                    "Importe inválido o faltante"
                )

            matched_client = None

            if client_name:
                matched_client = (
                    self._get_client_by_name(
                        client_name
                    )
                )

                if not matched_client:
                    row_errors.append(
                        (
                            f"Cliente '{client_name}' no "
                            "encontrado en la base de datos"
                        )
                    )

            # ----------------------------------------------------------
            # Estado
            # ----------------------------------------------------------

            raw_status = (
                row.get(status_col)
                if status_col is not None
                else None
            )

            normalized_status = _normalize_name(
                raw_status
            )

            is_paid = (
                normalized_status.startswith("pagado")
                or normalized_status == "pago"
            )

            # ----------------------------------------------------------
            # Método de pago
            # ----------------------------------------------------------

            payment_method_raw = None
            payment_method = "otro"

            # Si existen columnas Efectivo/Transferencia/etc.,
            # buscamos cuál tiene un importe.
            for actual_column, mapped_method in (
                method_columns
            ):
                method_amount = _to_decimal(
                    row.get(actual_column)
                )

                if (
                    method_amount is not None
                    and method_amount > 0
                ):
                    payment_method_raw = str(
                        actual_column
                    ).strip()

                    payment_method = mapped_method
                    break

            # Si no encontramos importe por método, usamos
            # una columna textual.
            if (
                payment_method_raw is None
                and payment_method_col is not None
            ):
                raw_method = row.get(
                    payment_method_col
                )

                if (
                    not _is_empty(raw_method)
                    and str(raw_method).strip()
                ):
                    payment_method_raw = str(
                        raw_method
                    ).strip()

                    payment_method = _map_payment_method(
                        payment_method_raw
                    )

            if (
                payment_method
                not in ALLOWED_PAYMENT_METHODS
            ):
                payment_method = "otro"

            # ----------------------------------------------------------
            # Solo importamos pagos.
            #
            # Pendiente de Pago NO crea una factura nueva porque la
            # factura ya sale de la pestaña del vendedor.
            # ----------------------------------------------------------

            if row_errors:
                errors.append(
                    ClientImportRowError(
                        row_number=row_number,
                        errors=[
                            (
                                f"[{registry_sheet}] {error}"
                            )
                            for error in row_errors
                        ],
                    )
                )
                continue

            if not is_paid:
                continue

            payment_date = (
                filled_dates[index]
                or date.today()
            )

            payments.append(
                {
                    "row_number": row_number,
                    "client": matched_client,
                    "client_name": client_name,
                    "amount": amount,
                    "payment_method": payment_method,
                    "payment_method_raw": (
                        payment_method_raw
                    ),
                    "payment_date": payment_date,
                }
            )

        return payments, errors

    # ==================================================================
    # Buscar facturas pendientes de un cliente
    # ==================================================================

    def _get_client_pending_invoices(
        self,
        client_id: int,
    ):
        """
        Obtiene documentos del cliente que todavía tienen saldo pendiente:
        remitos confirmados + presupuestos de pedido aprobados (los únicos
        que generan deuda real — ver sales_document_payment_rules). Se
        ordenan por fecha para aplicar el pago primero a los más antiguos.
        """

        invoices = (
            self.db.query(SalesInvoice)
            .filter(SalesInvoice.client_id == client_id)
            .filter(SalesInvoice.status == "confirmed")
            .all()
        )

        from app.services.sales_document_payment_rules import (
            _quote_has_registered_debt,
        )

        quotes = (
            self.db.query(SalesQuote)
            .filter(SalesQuote.client_id == client_id)
            .filter(SalesQuote.status == "approved")
            .all()
        )
        quotes = [
            q
            for q in quotes
            if q.order_id is not None
            or _quote_has_registered_debt(self.db, q.id)
        ]

        pending_invoices = []

        for doc_type, doc, doc_date in [
            ("sales_invoice", inv, inv.invoice_date) for inv in invoices
        ] + [
            ("sales_quote", q, q.quote_date) for q in quotes
        ]:
            total_amount = Decimal(str(doc.total_amount or 0))
            amount_paid = Decimal(str(doc.paid_amount or 0))
            outstanding = total_amount - amount_paid

            if outstanding > ZERO:
                pending_invoices.append(
                    {
                        "invoice": doc,
                        "document_type": doc_type,
                        "doc_date": doc_date,
                        "outstanding": outstanding,
                    }
                )

        pending_invoices.sort(key=lambda item: (item["doc_date"], item["invoice"].id))

        return pending_invoices

    # ==================================================================
    # Construir allocations para un pago
    # ==================================================================

    def _build_payment_allocations(
        self,
        *,
        client_id: int,
        payment_amount: Decimal,
    ) -> tuple[
        list[ClientPaymentAllocationItem],
        Decimal,
    ]:
        """
        Distribuye el pago entre documentos pendientes (remitos + presupuestos
        de pedido).

        Estrategia:
            FIFO:
            primero se cancelan los más antiguos.
        """

        remaining = payment_amount

        allocations: list[
            ClientPaymentAllocationItem
        ] = []

        pending_invoices = (
            self._get_client_pending_invoices(
                client_id
            )
        )

        for item in pending_invoices:
            if remaining <= ZERO:
                break

            invoice = item["invoice"]
            outstanding = item["outstanding"]

            allocation_amount = min(
                remaining,
                outstanding,
            )

            if allocation_amount <= ZERO:
                continue

            allocations.append(
                ClientPaymentAllocationItem(
                    invoice_id=invoice.id,
                    amount=allocation_amount,
                    document_type=item["document_type"],
                )
            )

            remaining -= allocation_amount

        return allocations, remaining

    # ==================================================================
    # Crear facturas agrupadas
    # ==================================================================

    def _filter_already_imported_rows(
        self,
        creation_ctx: list[dict],
        document_type: str,
    ) -> tuple[list[dict], int]:
        """
        Las hojas de vendedores son una lista corrida: no traen fecha por
        fila, así que en cada reimport pueden aparecer filas viejas (ya
        facturadas/cotizadas en un import anterior) mezcladas con filas
        nuevas. Acá se compara cada fila contra lo que ya existe en la
        base (mismo cliente + producto + cantidad + precio unitario, en
        un remito/presupuesto no cancelado) y se descartan las que ya
        fueron importadas, para no duplicar la venta.

        No es infalible (dos pedidos distintos con exactamente el mismo
        producto/cantidad/precio para el mismo cliente se seguirían
        viendo iguales), pero es la única señal disponible dado el
        formato de la planilla.
        """
        client_ids = list({
            ctx["client"].id
            for ctx in creation_ctx
            if ctx.get("client") is not None
        })

        if not client_ids:
            return creation_ctx, 0

        if document_type == "sales_quote":
            existing_rows = self.sales_quote_repo.get_item_rows_for_clients(client_ids)
        else:
            existing_rows = self.sales_invoice_repo.get_item_rows_for_clients(client_ids)

        already_imported = {
            row_signature(
                client_or_supplier_id=client_id,
                product_id=product_id,
                product_sku=None,
                product_name=None,
                quantity=quantity,
                unit_amount=unit_amount,
            )
            for client_id, product_id, quantity, unit_amount in existing_rows
        }

        new_ctx = []
        skipped = 0

        for ctx in creation_ctx:
            signature = row_signature(
                client_or_supplier_id=ctx["client"].id,
                product_id=ctx["product"].id,
                product_sku=None,
                product_name=None,
                quantity=int(ctx["quantity"]),
                unit_amount=ctx["unit_price"],
            )

            if signature in already_imported:
                skipped += 1
                continue

            new_ctx.append(ctx)

        return new_ctx, skipped

    def _create_grouped_sales_invoices(
        self,
        *,
        creation_ctx: list[dict],
        registry_sheet: str,
        current_user,
    ) -> list[int]:
        """
        Agrupa por:

            (sales_rep_id, client_id)

        Cada combinación genera UNA SalesInvoice con múltiples items.
        """

        grouped: dict[
            tuple[int, int],
            list[dict],
        ] = defaultdict(list)

        for item in creation_ctx:
            key = (
                item["sales_rep"].id,
                item["client"].id,
            )

            grouped[key].append(
                item
            )

        created_invoice_ids: list[int] = []

        for (
            sales_rep_id,
            client_id,
        ), items_ctx in grouped.items():

            sales_rep = items_ctx[0][
                "sales_rep"
            ]

            client = items_ctx[0][
                "client"
            ]

            # ----------------------------------------------------------
            # Agrupar productos repetidos dentro de la misma factura.
            #
            # Si el mismo producto aparece varias veces para el mismo
            # cliente/vendedor, se suman cantidades.
            # ----------------------------------------------------------

            products_grouped: dict[
                tuple[int, Decimal],
                dict,
            ] = {}

            for item in items_ctx:
                product = item["product"]

                key = (
                    product.id,
                    item["unit_price"],
                )

                if key not in products_grouped:
                    products_grouped[key] = {
                        "product": product,
                        "quantity": ZERO,
                        "unit_price": item[
                            "unit_price"
                        ],
                    }

                products_grouped[key][
                    "quantity"
                ] += item["quantity"]

            # ----------------------------------------------------------
            # Items y totales
            # ----------------------------------------------------------

            items_data: list[dict] = []
            schema_items: list[
                SalesInvoiceItemCreate
            ] = []

            total_amount = ZERO
            total_cost = ZERO

            for grouped_product in (
                products_grouped.values()
            ):
                product = grouped_product[
                    "product"
                ]

                quantity = grouped_product[
                    "quantity"
                ]

                unit_price = grouped_product[
                    "unit_price"
                ]

                unit_cost = Decimal(
                    str(product.unit_cost or 0)
                )

                subtotal = (
                    unit_price * quantity
                )

                subtotal_cost = (
                    unit_cost * quantity
                )

                margin_amount = (
                    subtotal - subtotal_cost
                )

                total_amount += subtotal
                total_cost += subtotal_cost

                items_data.append(
                    {
                        "product_id": product.id,
                        "product_name": product.name,
                        "product_brand": product.brand,
                        "product_sku": product.sku,
                        "quantity": int(quantity),
                        "unit_cost": unit_cost,
                        "unit_price": unit_price,
                        "subtotal_cost": subtotal_cost,
                        "subtotal": subtotal,
                        "margin_amount": margin_amount,
                    }
                )

                schema_items.append(
                    SalesInvoiceItemCreate(
                        product_id=product.id,
                        product_name=product.name,
                        product_brand=product.brand,
                        product_sku=product.sku,
                        quantity=int(quantity),
                    )
                )

            margin_amount = (
                total_amount - total_cost
            )

            invoice_date = min(
                item["sale_date"]
                for item in items_ctx
            )

            source_sheets = sorted(
                {
                    item["sheet_name"]
                    for item in items_ctx
                }
            )

            client_snapshot = ClientSnapshot(
                id=client.id,
                name=client.name,
            ).model_dump()

            sales_rep_snapshot = (
                SalesRepSnapshot(
                    id=sales_rep.id,
                    name=sales_rep.name,
                    email=getattr(
                        sales_rep,
                        "email",
                        None,
                    ),
                ).model_dump()
            )

            obj_in = SalesInvoiceCreate(
                sales_type=SalesType.B2B,
                client_id=client.id,
                sales_rep_id=sales_rep_id,
                invoice_number=(
                    self.sales_invoice_repo
                    .generate_invoice_number()
                ),
                invoice_date=invoice_date,
                notes=(
                    "Importado desde Excel — "
                    f"pestaña(s): {', '.join(source_sheets)}"
                ),
                items=schema_items,
            )

            invoice = (
                self.sales_invoice_repo.create(
                    obj_in=obj_in,
                    total_cost=total_cost,
                    total_amount=total_amount,
                    margin_amount=margin_amount,
                    items_data=items_data,
                    sales_rep_id=sales_rep_id,
                    client_snapshot=client_snapshot,
                    client_branch_snapshot=None,
                    sales_rep_snapshot=(
                        sales_rep_snapshot
                    ),
                )
            )

            self.db.flush()

            # Confirmar:
            # - descuenta stock
            # - crea movimiento/deuda correspondiente
            self.sales_invoice_service.update_status(
                invoice.id,
                "confirmed",
                current_user,
            )

            self.db.flush()

            created_invoice_ids.append(
                invoice.id
            )

        return created_invoice_ids

    # ==================================================================
    # Crear presupuestos agrupados (document_type == "sales_quote")
    # ==================================================================

    def _create_grouped_sales_quotes(
        self,
        *,
        creation_ctx: list[dict],
        registry_sheet: str,
        current_user,
    ) -> list[int]:
        """
        Igual que _create_grouped_sales_invoices (agrupa por vendedor +
        cliente, una fila por producto repetido), pero crea SalesQuote en
        vez de SalesInvoice: no toca stock (un presupuesto no reparte
        mercadería) y no pasa por update_status("confirmed"), que es un
        estado propio de los remitos.

        El presupuesto nace 'approved' y registra su deuda en la cuenta
        corriente del cliente igual que uno generado por un pedido (ver
        SalesQuoteService._register_quote_receivable), así que después
        puede recibir cobros como cualquier otro documento vigente.
        """

        grouped: dict[
            tuple[int, int],
            list[dict],
        ] = defaultdict(list)

        for item in creation_ctx:
            key = (
                item["sales_rep"].id,
                item["client"].id,
            )

            grouped[key].append(item)

        created_quote_ids: list[int] = []

        for (
            sales_rep_id,
            client_id,
        ), items_ctx in grouped.items():

            sales_rep = items_ctx[0]["sales_rep"]
            client = items_ctx[0]["client"]

            products_grouped: dict[
                tuple[int, Decimal],
                dict,
            ] = {}

            for item in items_ctx:
                product = item["product"]

                key = (
                    product.id,
                    item["unit_price"],
                )

                if key not in products_grouped:
                    products_grouped[key] = {
                        "product": product,
                        "quantity": ZERO,
                        "unit_price": item["unit_price"],
                    }

                products_grouped[key]["quantity"] += item["quantity"]

            items_data: list[dict] = []

            total_amount = ZERO
            total_cost = ZERO

            for grouped_product in products_grouped.values():
                product = grouped_product["product"]
                quantity = grouped_product["quantity"]
                unit_price = grouped_product["unit_price"]

                unit_cost = Decimal(str(product.unit_cost or 0))
                subtotal = unit_price * quantity
                subtotal_cost = unit_cost * quantity
                margin_amount = subtotal - subtotal_cost

                total_amount += subtotal
                total_cost += subtotal_cost

                items_data.append(
                    {
                        "product_id": product.id,
                        "product_name": product.name,
                        "product_brand": product.brand,
                        "product_sku": product.sku,
                        "quantity": int(quantity),
                        "unit_cost": unit_cost,
                        "unit_price": unit_price,
                        "subtotal_cost": subtotal_cost,
                        "subtotal": subtotal,
                        "margin_amount": margin_amount,
                    }
                )

            margin_amount = total_amount - total_cost

            quote_date = min(item["sale_date"] for item in items_ctx)

            source_sheets = sorted(
                {item["sheet_name"] for item in items_ctx}
            )

            client_snapshot = ClientSnapshot(
                id=client.id,
                name=client.name,
            ).model_dump()

            sales_rep_snapshot = SalesRepSnapshot(
                id=sales_rep.id,
                name=sales_rep.name,
                email=getattr(sales_rep, "email", None),
            ).model_dump()

            header = {
                "order_id": None,
                "sales_type": SalesType.B2B,
                "client_id": client.id,
                "sales_rep_id": sales_rep_id,
                "client_snapshot": client_snapshot,
                "sales_rep_snapshot": sales_rep_snapshot,
                "quote_number": _generate_invoice_number(sales_rep.name),
                "quote_date": quote_date,
                "status": "approved",
                "payment_status": "pending",
                "paid_amount": ZERO,
                "total_cost": total_cost,
                "total_amount": total_amount,
                "margin_amount": margin_amount,
                "currency": "ARS",
                "notes": (
                    "Importado desde Excel — "
                    f"pestaña(s): {', '.join(source_sheets)}"
                ),
            }

            quote = self.sales_quote_service.sales_quote_repo.create(
                header=header,
                items_data=items_data,
            )

            self.sales_quote_service._register_quote_receivable(
                quote, current_user
            )

            self.db.flush()

            created_quote_ids.append(quote.id)

        return created_quote_ids

    # ==================================================================
    # Registrar pagos
    # ==================================================================

    def _register_imported_payments(
        self,
        *,
        payments: list[dict],
        current_user,
    ) -> list[ClientImportPaymentResult]:
        results: list[ClientImportPaymentResult] = []

        for payment in payments:

            client = payment["client"]

            allocations, remaining = (
                self._build_payment_allocations(
                    client_id=client.id,
                    payment_amount=payment["amount"],
                )
            )

            # Si no encontramos deuda suficiente, no asignamos el pago
            # a una factura inexistente. Lo registramos igualmente como
            # pago sin allocations para conservar el movimiento.
            #
            # Esto permite importar saldos históricos anteriores a las
            # facturas que existen actualmente en el sistema.
            notes = (
                "Cobro importado desde Excel — "
                f"fila {payment['row_number']}"
            )

            if remaining > ZERO:
                notes += (
                    f". Monto sin asignar: {remaining}"
                )

            self.client_account_movement_service.register_payment(
                client_id=client.id,
                data=ClientPaymentCreate(
                    amount=payment["amount"],
                    payment_method=payment[
                        "payment_method"
                    ],
                    notes=notes,
                    allocations=allocations,
                ),
                current_user=current_user,
            )

            self.db.flush()

            allocated_amount = payment["amount"] - remaining

            invoice_numbers: list[str] = []

            if allocations:
                invoice_alloc_ids = [
                    a.invoice_id
                    for a in allocations
                    if a.document_type == "sales_invoice"
                ]
                quote_alloc_ids = [
                    a.invoice_id
                    for a in allocations
                    if a.document_type == "sales_quote"
                ]

                if invoice_alloc_ids:
                    invoice_numbers += [
                        inv.invoice_number
                        for inv in self.sales_invoice_repo.get_by_ids(
                            invoice_alloc_ids
                        )
                    ]

                if quote_alloc_ids:
                    invoice_numbers += [
                        q.quote_number
                        for q in (
                            self.db.query(SalesQuote)
                            .filter(SalesQuote.id.in_(quote_alloc_ids))
                            .all()
                        )
                    ]

            results.append(
                ClientImportPaymentResult(
                    row_number=payment["row_number"],
                    client_name=client.name,
                    amount=payment["amount"],
                    allocated_amount=allocated_amount,
                    unassigned_amount=remaining,
                    invoice_numbers=invoice_numbers,
                )
            )

        return results

    # ==================================================================
    # Clientes
    # ==================================================================

    def import_client_sales(
        self,
        *,
        file_bytes: bytes,
        sheet_name: str | None,
        document_type: str = "sales_invoice",
        dry_run: bool,
        current_user,
    ) -> ClientImportResult:
        """
        Importa un Excel completo usando dos fuentes:

        1. Pestañas de vendedores:
        Son la fuente de las ventas reales:
            vendedor + cliente + producto + cantidad + precio

        Se crean SalesInvoice / SalesQuote (según la columna "document" de
        cada fila; por defecto, document_type) agrupadas por:
            (sales_rep_id, client_id)

        2. REGISTRO CLIENTES:
        Se usa como cuenta corriente.
        Las filas Pagado se importan como pagos.
        Las filas Pendiente NO crean otra factura.

        Las filas válidas pueden importarse aunque existan
        errores en otras filas.

        Si dry_run=True, solamente devuelve el preview.
        """

        # --------------------------------------------------------------
        # Leer Excel
        # --------------------------------------------------------------

        try:
            excel = pd.ExcelFile(
                io.BytesIO(file_bytes)
            )
        except Exception as exc:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                f"Error al leer el Excel: {exc}",
            )

        # --------------------------------------------------------------
        # Resolver REGISTRO CLIENTES
        # --------------------------------------------------------------

        if sheet_name:
            registry_sheet = next(
                (
                    sheet
                    for sheet in excel.sheet_names
                    if _normalize_name(sheet)
                    == _normalize_name(sheet_name)
                ),
                None,
            )
        else:
            registry_sheet = next(
                (
                    sheet
                    for sheet in excel.sheet_names
                    if (
                        "registro" in _normalize_name(sheet)
                        and "client" in _normalize_name(sheet)
                    )
                ),
                None,
            )

        if not registry_sheet:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                (
                    "No se encontró la hoja "
                    "'REGISTRO CLIENTES'. "
                    f"Hojas disponibles: "
                    f"{', '.join(excel.sheet_names)}"
                ),
            )

        # --------------------------------------------------------------
        # 1. Analizar ventas de vendedores
        #
        # document_type es el tipo POR DEFECTO: se usa en las filas cuya
        # columna "document" está vacía (o si la hoja no la tiene).
        # --------------------------------------------------------------

        if document_type not in ("sales_invoice", "sales_quote"):
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                "document_type inválido (usar sales_invoice o sales_quote)",
            )

        (
            sales_rows,
            sales_errors,
            creation_ctx,
        ) = self._parse_sales_rep_sheets(
            excel=excel,
            registry_sheet=registry_sheet,
            default_document_type=document_type,
        )

        # --------------------------------------------------------------
        # 2. Analizar REGISTRO CLIENTES
        # --------------------------------------------------------------

        (
            payments,
            registry_errors,
        ) = self._parse_client_registry(
            excel=excel,
            registry_sheet=registry_sheet,
        )

        all_errors = [
            *sales_errors,
            *registry_errors,
        ]

        # --------------------------------------------------------------
        # Crear resultado del preview/import
        # --------------------------------------------------------------

        result = ClientImportResult(
            dry_run=dry_run,
            sheet_name=registry_sheet,
            total_rows_read=(
                len(sales_rows)
                + len(payments)
                + len(all_errors)
            ),
            rows_to_import=sales_rows,
            rows_with_errors=all_errors,
            document_type=document_type,
        )

        # --------------------------------------------------------------
        # Preview
        # --------------------------------------------------------------

        if dry_run:
            return result

        # --------------------------------------------------------------
        # Si no hay registros válidos, no hay nada que importar.
        #
        # OJO:
        # No bloqueamos la importación porque existan errores.
        # Las filas válidas sí se procesan.
        # --------------------------------------------------------------

        if not creation_ctx and not payments:
            return result

        # --------------------------------------------------------------
        # 2.5. Descartar filas de venta que ya fueron importadas antes
        # (la planilla de vendedores es una lista corrida sin fecha por
        # fila, así que reimportarla trae mezcladas filas viejas y nuevas).
        # --------------------------------------------------------------

        # Cada fila lleva su propio tipo (columna "document"), así que un mismo
        # Excel puede crear remitos y presupuestos. Cada grupo se filtra contra
        # lo ya importado de SU tipo y se crea por separado.
        if creation_ctx:
            for group_type in ("sales_invoice", "sales_quote"):
                group_ctx = [
                    ctx
                    for ctx in creation_ctx
                    if ctx["document_type"] == group_type
                ]

                if not group_ctx:
                    continue

                group_ctx, skipped_count = (
                    self._filter_already_imported_rows(
                        creation_ctx=group_ctx,
                        document_type=group_type,
                    )
                )
                result.rows_skipped_already_imported += skipped_count

                if not group_ctx:
                    continue

                # ----------------------------------------------------------
                # 3. Crear SalesInvoice / SalesQuote agrupadas
                # ----------------------------------------------------------

                if group_type == "sales_quote":
                    result.created_sales_quote_ids.extend(
                        self._create_grouped_sales_quotes(
                            creation_ctx=group_ctx,
                            registry_sheet=registry_sheet,
                            current_user=current_user,
                        )
                    )
                else:
                    result.created_sales_invoice_ids.extend(
                        self._create_grouped_sales_invoices(
                            creation_ctx=group_ctx,
                            registry_sheet=registry_sheet,
                            current_user=current_user,
                        )
                    )

        # --------------------------------------------------------------
        # 4. Aplicar pagos
        #
        # Las facturas se crean antes para que los pagos puedan
        # asignarse a las facturas pendientes.
        # --------------------------------------------------------------

        if payments:
            result.payments_applied = (
                self._register_imported_payments(
                    payments=payments,
                    current_user=current_user,
                )
            )

        self.db.flush()

        return result