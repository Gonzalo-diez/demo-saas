from __future__ import annotations

import os
import re
import tempfile
from decimal import Decimal, InvalidOperation
from io import BytesIO
from typing import Iterator

import pdfplumber
from openpyxl import Workbook
from openpyxl.styles import (
    Alignment,
    Border,
    Font,
    PatternFill,
    Side,
)
from openpyxl.utils import get_column_letter

# ---------------------------------------------------------------------------
# Mapeos y constantes del proveedor
# ---------------------------------------------------------------------------

# Mapeo de encabezados de sección del PDF al NOMBRE de categoría que se propone en
# el Excel. Al importar, cada nombre se busca entre las categorías de la distribuidora
# y, si no existe, se crea privada (la distribuidora decide después si la publica).
# Agregar nuevas secciones aquí si el proveedor las incorpora en el futuro.
PDF_SECTION_TO_CATEGORY: dict[str, str] = {
    "CIGARRILLOS":   "Cigarrillos Eco",
    "BAT MODO":      "Masalin Bat",
    "MASSALIN":      "Masalin Bat",
    "TABACO":        "Tabaco & Accesorios",
    "PAPEL":         "Tabaco & Accesorios",
    "FILTROS":       "Tabaco & Accesorios",
    "MAQUINA":       "Tabaco & Accesorios",
    "ENCENDEDOR":    "Tabaco & Accesorios",
    "PUROS":         "Tabaco & Accesorios",
    "MEDICAMENTOS":  "Analgésicos",
    "PEGAMENTOS":    "Pegamentos",
    "PILAS":         "Pilas",
    "PRESERVATIVOS": "Preservativos",
}

# Marcas conocidas en el formato de este proveedor.
# Agregar nuevas marcas aquí si el proveedor las incorpora en el futuro.
KNOWN_BRANDS: set[str] = {
    "122", "123", "125", "127",
    "NOBLEZA", "SARANDI", "T&H", "ESPERT", "STAMPS", "SMOKING",
    "CLIPPER", "BLUNT REY", "BRONWAY", "ZODIAC", "DROGUERIA",
    "ARGENTO", "HAASEN", "V HAASEN", "TABES", "SAYRI",
}

# Líneas de encabezado/pie de página a ignorar
SKIP_LINES: frozenset[str] = frozenset({
    "Código Descripción Marca LISTA 2",
    "Código Descripción Marca",
    "Código Descripción LISTA 2",
    "LISTA 2",
    "Código Descripción",
})

# Regex
_SECTION_RE = re.compile(r"^([A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑ\s/&]{1,38})$")
_PRICE_RE   = re.compile(r"\s+([\d\.]+,\d+)\s*$")
_CODE_RE    = re.compile(r"^(\S+)\s+(.+)$")


# ---------------------------------------------------------------------------
# Parsing interno
# ---------------------------------------------------------------------------

def _parse_price(price_str: str) -> Decimal | None:
    """Convierte '1.234,56' o '251.425,0' a Decimal."""
    try:
        return Decimal(price_str.replace(".", "").replace(",", "."))
    except InvalidOperation:
        return None


def _parse_line(line: str) -> dict | None:
    """
    Extrae (code, name, brand, unit_cost) de una línea de producto.
    Retorna None si la línea no tiene el formato esperado.
    """
    price_m = _PRICE_RE.search(line)
    if not price_m:
        return None

    before = line[: price_m.start()].strip()
    code_m = _CODE_RE.match(before)
    if not code_m:
        return None

    code       = code_m.group(1)
    desc_brand = code_m.group(2).strip()

    brand = ""
    desc  = desc_brand

    # Separar marca: probar 2 tokens primero, luego 1
    for brand_len in (2, 1):
        tokens = desc_brand.split()
        if len(tokens) > brand_len:
            candidate = " ".join(tokens[-brand_len:])
            if candidate in KNOWN_BRANDS:
                brand = candidate
                desc  = " ".join(tokens[:-brand_len])
                break

    price = _parse_price(price_m.group(1))
    if price is None:
        return None

    return {
        "code":      code,
        "name":      desc.strip(),
        "brand":     brand,
        "unit_cost": price,
    }


def _is_section_header(line: str) -> bool:
    return bool(_SECTION_RE.match(line)) and not _PRICE_RE.search(line)


def _iter_products_from_path(pdf_path: str) -> Iterator[dict]:
    """
    Itera sobre todos los productos del PDF (dado como path en disco)
    que correspondan a una categoría habilitada en el backend.
    Yields dicts con keys: name, description, brand, category, unit_cost.
    """
    current_category: str | None = None

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            raw_text = page.extract_text() or ""
            for line in raw_text.split("\n"):
                line = line.strip()

                if not line:
                    continue
                if line.startswith("Listado de") or line.startswith("Pág."):
                    continue
                if line in SKIP_LINES:
                    continue

                # Detectar cambio de sección
                if _is_section_header(line):
                    current_category = PDF_SECTION_TO_CATEGORY.get(line)
                    continue

                # Solo procesar si la sección está mapeada
                if current_category is None:
                    continue

                row = _parse_line(line)
                if row is None:
                    continue
                if row["unit_cost"] <= 0:
                    continue  # Excluir precios 0 (descontinuados, sin stock, etc.)

                yield {
                    "name":        row["name"],
                    "description": row["name"],  # espejo inicial; el equipo lo ajusta
                    "brand":       row["brand"],
                    "category":    current_category,
                    "unit_cost":   row["unit_cost"],
                }


def _iter_products(source: str | bytes) -> Iterator[dict]:
    """
    Wrapper que acepta tanto un path (str) como los bytes crudos del PDF.
    Cuando recibe bytes escribe un archivo temporal, lo procesa y lo elimina.
    """
    if isinstance(source, bytes):
        tmp_fd, tmp_path = tempfile.mkstemp(suffix=".pdf")
        try:
            os.write(tmp_fd, source)
            os.close(tmp_fd)
            yield from _iter_products_from_path(tmp_path)
        finally:
            os.unlink(tmp_path)
    else:
        yield from _iter_products_from_path(source)


# ---------------------------------------------------------------------------
# Estilos Excel
# ---------------------------------------------------------------------------

_COLUMNS = [
    ("name",        "name",        45, None),
    ("description", "description",   45, None),
    ("brand",       "brand",         20, None),
    ("category",    "category",     22, None),
    ("unit_cost",   "unit_cost", 18, None),
    ("unit_price",  "unit_price",  18, ""),
    ("stock_current",       "stock_current", 16, "0"),
    ("stock_min",   "stock_min",  16, "0"),
    ("sku",         "sku",           18, ""),
    ("image_url", "image_url", 45, ""),
    ("is_active", "is_active", 12, False),
]

_HEADER_FILL  = PatternFill("solid", fgColor="1F3864")
_LOCKED_FILL  = PatternFill("solid", fgColor="F2F2F2")
_PENDING_FILL = PatternFill("solid", fgColor="FFF2CC")
_HEADER_FONT  = Font(name="Arial", bold=True, color="FFFFFF", size=10)
_DATA_FONT    = Font(name="Arial", size=10)
_BORDER_SIDE  = Side(style="thin", color="CCCCCC")
_BORDER       = Border(
    left=_BORDER_SIDE, right=_BORDER_SIDE,
    top=_BORDER_SIDE,  bottom=_BORDER_SIDE,
)
_CENTER = Alignment(horizontal="center", vertical="center", wrap_text=True)
_LEFT   = Alignment(horizontal="left",   vertical="center", wrap_text=True)


def _apply_header(ws, col_idx: int, label: str) -> None:
    cell           = ws.cell(row=1, column=col_idx, value=label)
    cell.font      = _HEADER_FONT
    cell.fill      = _HEADER_FILL
    cell.border    = _BORDER
    cell.alignment = _CENTER


# ---------------------------------------------------------------------------
# Función pública
# ---------------------------------------------------------------------------

def build_excel(source: str | bytes) -> bytes:
    """
    Parsea el PDF (path o bytes) y devuelve los bytes de un archivo .xlsx
    listo para ser completado por el equipo e importado al backend con
    POST /api/products/import/preview → /import/commit-file.

    Args:
        source: path al archivo PDF (str) o contenido binario del PDF (bytes).

    Returns:
        Bytes del archivo .xlsx generado.
    """
    products = list(_iter_products(source))
    products.sort(key=lambda p: (p["category"], p["name"]))

    wb = Workbook()

    # ------------------------------------------------------------------ #
    #  Hoja 1: Productos                                                   #
    # ------------------------------------------------------------------ #
    ws = wb.active
    ws.title = "Productos"
    ws.freeze_panes = "A2"
    ws.row_dimensions[1].height = 32

    for col_idx, (key, label, width, _default) in enumerate(_COLUMNS, start=1):
        _apply_header(ws, col_idx, label)
        ws.column_dimensions[get_column_letter(col_idx)].width = width

    for row_idx, product in enumerate(products, start=2):
        for col_idx, (key, _label, _width, default) in enumerate(_COLUMNS, start=1):
            raw = product.get(key, default if default is not None else "")

            if key == "unit_cost" and isinstance(raw, Decimal):
                value = float(raw)
            elif raw is None:
                value = ""
            else:
                value = raw

            cell           = ws.cell(row=row_idx, column=col_idx, value=value)
            cell.font      = _DATA_FONT
            cell.border    = _BORDER
            cell.alignment = (
                _CENTER
                if key in ("unit_cost", "unit_price", "stock", "stock_min", "is_active", "sku")
                else _LEFT
            )

            if key in ("sku", "unit_price", "stock_current", "stock_min", "image_url"):
                cell.fill = _PENDING_FILL
            elif key in ("stock", "stock_min", "is_active"):
                cell.fill = _LOCKED_FILL

    # ------------------------------------------------------------------ #
    #  Hoja 2: Instrucciones                                               #
    # ------------------------------------------------------------------ #
    wi = wb.create_sheet("Instrucciones")
    wi.column_dimensions["A"].width = 80

    instrucciones = [
        ("INSTRUCCIONES DE COMPLETADO", True),
        ("", False),
        ("1. CAMPOS EN AMARILLO → deben ser completados por el equipo:", True),
        ("   • SKU: código interno del producto (puede coincidir con el código del proveedor).", False),
        ("   • Precio venta: precio al que se venderá al cliente (mayor al costo).", False),
        ("", False),
        ("2. CAMPOS EN GRIS → vienen pre-completados con valores por defecto:", True),
        ("   • Stock inicial: 0 (ajustar si hay stock existente).", False),
        ("   • Stock mínimo: 0 (ajustar según política de reposición).", False),
        ("   • Activo: false (cambiar a true solo los productos que se van a activar).", False),
        ("", False),
        ("3. CAMPOS DE SOLO LECTURA → extraídos del PDF del proveedor:", True),
        ("   • Nombre, Descripción, Marca, Categoría, Costo unitario.", False),
        ("   • Editar solo si hay errores de lectura del PDF.", False),
        ("", False),
        ("4. IMPORTACIÓN:", True),
        ("   • Guardar este archivo como .xlsx.", False),
        ("   • Subir en /api/products/import/preview para revisar, luego /import/commit-file.", False),
        ("   • El sistema validará SKU únicos y campos requeridos.", False),
        ("", False),
        ("5. CATEGORÍAS:", True),
        ("   • Si el nombre coincide con una categoría que ya creaste, se usa esa", False),
        ("     (con su configuración de público/privado).", False),
        ("   • Si no existe, se crea una categoría nueva PRIVADA: los productos no", False),
        ("     aparecen en el catálogo de clientes hasta que la publiques desde", False),
        ("     Categorías. Mientras tanto quedan disponibles para venta B2B.", False),
    ]

    for i, (text, bold) in enumerate(instrucciones, start=1):
        cell           = wi.cell(row=i, column=1, value=text)
        cell.font      = Font(name="Arial", bold=bold, size=10)
        cell.alignment = _LEFT

    # ------------------------------------------------------------------ #
    #  Hoja 3: Resumen por categoría                                       #
    # ------------------------------------------------------------------ #
    wr = wb.create_sheet("Resumen")
    wr.column_dimensions["A"].width = 30
    wr.column_dimensions["B"].width = 18
    wr.column_dimensions["C"].width = 22

    for col_idx, label in enumerate(["Categoría", "Cantidad", "Costo promedio"], start=1):
        _apply_header(wr, col_idx, label)

    counts: dict[str, list] = {}
    for p in products:
        counts.setdefault(p["category"], []).append(float(p["unit_cost"]))

    for row_idx, cat in enumerate(sorted(counts.keys()), start=2):
        costs = counts[cat]
        avg   = sum(costs) / len(costs)
        wr.cell(row=row_idx, column=1, value=cat).font = _DATA_FONT
        wr.cell(row=row_idx, column=2, value=len(costs)).font                    = _DATA_FONT
        cell               = wr.cell(row=row_idx, column=3, value=round(avg, 2))
        cell.font          = _DATA_FONT
        cell.number_format = "#,##0.00"

    last = len(counts) + 2
    wr.cell(row=last, column=1, value="TOTAL").font         = Font(name="Arial", bold=True, size=10)
    wr.cell(row=last, column=2, value=len(products)).font   = Font(name="Arial", bold=True, size=10)

    buf = BytesIO()
    wb.save(buf)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Punto de entrada para uso directo / testing
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Uso: python supplier_pdf_import_service.py <ruta_pdf> [ruta_salida.xlsx]")
        sys.exit(1)

    pdf_path  = sys.argv[1]
    xlsx_path = sys.argv[2] if len(sys.argv) > 2 else "productos_importacion.xlsx"

    print(f"Procesando: {pdf_path}")
    data = build_excel(pdf_path)

    with open(xlsx_path, "wb") as f:
        f.write(data)

    print(f"Archivo generado: {xlsx_path}")