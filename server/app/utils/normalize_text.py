import re
import unicodedata

def normalize_text(value: str | None) -> str | None:
    if value is None:
        return None

    value = value.strip().lower()
    value = unicodedata.normalize("NFKD", value)
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    value = re.sub(r"\s+", " ", value)

    return value