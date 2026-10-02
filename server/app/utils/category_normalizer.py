import re
import unicodedata

CATEGORY_ALIASES = {
    "sin clasificar": "Sin Clasificar",
    # Analgésicos
    "analgesicos": "analgesicos",
    "analgesico": "analgesicos",
    "analgesicos y farmacia": "analgesicos",
    "farmacia": "analgesicos",
    "medicamentos": "analgesicos",

    # Cigarrillos Eco
    "cigarrillos eco": "cigarrillos eco",
    "cigarrillos economicos": "cigarrillos eco",
    "cigarrillos economico": "cigarrillos eco",
    "eco": "cigarrillos eco",
    "economicos": "cigarrillos eco",

    # Masalin Bat
    "masalin bat": "masalin bat",
    "masalin y bat": "masalin bat",
    "masalin & bat": "masalin bat",
    "masalin": "masalin bat",
    "bat": "masalin bat",

    # Tabaco & Accesorios
    "tabaco accesorios": "tabaco accesorios",
    "tabaco y accesorios": "tabaco accesorios",
    "tabaco & accesorios": "tabaco accesorios",
    "tabacos y accesorios": "tabaco accesorios",
    "tabacos accesorios": "tabaco accesorios",
    "tabaco": "tabaco accesorios",
    "accesorios tabaco": "tabaco accesorios",
    "accesorios para fumar": "tabaco accesorios",
    "armado": "tabaco accesorios",
    "papelillos": "tabaco accesorios",
    "filtros": "tabaco accesorios",
    "encendedores": "tabaco accesorios",
    
    # Pegamentos
    "pegamento": "pegamentos",
    "pegamentos": "pegamentos",
    
    # Pilas
    "pila": "pilas",
    "pilas": "pilas",
    "bateria": "pilas",
    "baterias": "pilas",
    
    # Preservativos
    "condon": "preservativos",
    "condones": "preservativos",
    "preservativo": "preservativos",
    "preservativos": "preservativos", 
}

CATEGORY_LABELS = {
    "sin clasificar": "Sin Clasificar",
    "analgesicos": "Analgésicos",
    "cigarrillos eco": "Cigarrillos Eco",
    "masalin bat": "Masalin Bat",
    "tabaco accesorios": "Tabaco & Accesorios",
    "pegamentos": "pegamentos",
    "pilas": "pilas",
    "preservativos": "preservativos"
}

# Categorías cuya venta está regulada por la Ley 26.687 (control de
# tabaco). Los pedidos que incluyan productos de estas categorías
# exigen verificación de edad (DNI + declaración jurada) en el checkout.
REGULATED_CATEGORIES = {
    "cigarrillos eco",
    "masalin bat",
    "tabaco accesorios",
}


def is_regulated_category(value: str | None) -> bool:
    """
    Chequea si la categoría de un producto activo requiere verificación
    de edad en el checkout. No debe explotar si la categoría no está en
    la whitelist (productos "libres"/no catálogo también pueden llegar
    acá si terminan activos para venta B2B).
    """
    try:
        canonical = canonicalize_category(value) if value else None
    except ValueError:
        return False
    return canonical in REGULATED_CATEGORIES


def is_catalog_category(value: str | None) -> bool:
    """
    True si `value` es una de las categorías "seteadas" (whitelist), es
    decir, una categoría que sí se va a mostrar en el catálogo online.
    Cualquier otro valor se considera una categoría libre/interna (para
    productos de venta B2B que no van al catálogo).
    """
    if not value:
        return False

    try:
        return canonicalize_category(value) is not None
    except ValueError:
        return False


def normalize_free_category(value: str | None) -> str | None:
    """
    Normaliza (trim + colapsa espacios) una categoría libre/interna sin
    validarla contra la whitelist de catálogo. Se usa para productos que
    no van a estar publicados en la página (import, remitos, presupuestos,
    creación manual de productos "no catálogo").
    """
    if value is None:
        return None

    cleaned = " ".join(value.strip().split())
    return cleaned or None


def resolve_category_value(value: str | None) -> str | None:
    """
    Punto único de entrada para guardar `Product.category` en cualquier
    flujo de creación/edición (alta manual, import, remitos/presupuestos).

    - Si `value` matchea (por alias) una categoría ya seteada del
      catálogo, devuelve su forma canónica (igual que antes), para que
      el catálogo online, los filtros y `is_regulated_category` sigan
      funcionando sin cambios.
    - Si no matchea ninguna categoría seteada, la trata como categoría
      libre/interna: no la rechaza, solo la normaliza (trim/espacios) y
      la guarda tal cual la escribieron. Ese producto nunca va a
      aparecer en el catálogo online (ver `is_catalog_category`), pero
      puede quedar activo para venta B2B.
    """
    if value is None:
        return None

    try:
        return canonicalize_category(value)
    except ValueError:
        return normalize_free_category(value)


def _normalize_base(value: str | None) -> str | None:
    if value is None:
        return None

    value = value.strip().lower()
    if not value:
        return None

    value = unicodedata.normalize("NFD", value)
    value = "".join(char for char in value if unicodedata.category(char) != "Mn")

    value = value.replace("&", " y ")

    value = re.sub(r"[^a-z0-9\s-]", " ", value)
    value = re.sub(r"[\-_]+", " ", value)
    value = re.sub(r"\s+", " ", value).strip()

    return value or None


def canonicalize_category(value: str | None) -> str | None:
    if value and value.strip() == "Sin Clasificar":
        return "Sin Clasificar"
        
    normalized = _normalize_base(value)
    if normalized is None:
        return None

    # Ahora esto cubrirá "sin clasificar", "Sin clasificar", "SIN CLASIFICAR", etc.
    canonical = CATEGORY_ALIASES.get(normalized)
    
    if canonical is None:
        raise ValueError(f"Categoría no permitida: {value}")

    return canonical


def get_category_label(value: str | None) -> str | None:
    canonical = canonicalize_category(value)
    if canonical is None:
        return None

    return CATEGORY_LABELS.get(canonical, canonical.title())


def get_all_canonical_categories() -> list[str]:
    return sorted(CATEGORY_LABELS.keys())


def normalize_category_key(value: str | None) -> str | None:
    """
    Clave de comparación de una categoría (minúsculas, sin tildes, `&` -> `y`,
    sin símbolos). Es la misma normalización que usa `canonicalize_category`,
    expuesta para que el frontend pueda replicarla al detectar colisiones con
    alias de categorías de catálogo.
    """
    return _normalize_base(value)


def get_catalog_category_options() -> list[dict[str, str]]:
    """Categorías seteadas de catálogo (sin el placeholder "Sin Clasificar")."""
    return [
        {"value": key, "label": CATEGORY_LABELS[key]}
        for key in sorted(CATEGORY_LABELS.keys())
        if key != "sin clasificar"
    ]


def get_catalog_category_aliases() -> dict[str, str]:
    """
    Mapa alias -> categoría canónica de catálogo. Sirve para avisar en el
    alta manual cuando el nombre de una categoría "nueva" en realidad coincide
    con una categoría de catálogo (y por lo tanto saldría en la tienda online).
    """
    return {
        alias: canonical
        for alias, canonical in CATEGORY_ALIASES.items()
        if canonical != "Sin Clasificar" and alias != "sin clasificar"
    }


def get_category_options() -> list[dict[str, str]]:
    return [
        {"value": key, "label": CATEGORY_LABELS[key]}
        for key in sorted(CATEGORY_LABELS.keys())
    ]