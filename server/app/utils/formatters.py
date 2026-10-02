import re

def normalize_tax_id(tax_id: str | None) -> str | None:
    if not tax_id:
        return None
    return re.sub(r"\D", "", tax_id)

def normalize_email(email: str | None) -> str | None:
    if not email:
        return None
    return email.strip().lower()

def normalize_phone(phone: str | int | float | None) -> str | None:
    if phone is None:
        return None

    phone = str(phone).strip()

    if not phone:
        return None

    # Excel suele convertir teléfonos a float
    if phone.endswith(".0"):
        phone = phone[:-2]

    return re.sub(r"\D", "", phone)