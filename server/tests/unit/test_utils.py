"""
test_utils.py — Tests de utilidades puras (sin BD ni HTTP).
Cubren: slugify, normalize_text, formatters, geo.
"""
import pytest

# ═══════════════════════════════════════════════════════════════════════════
# slugify
# ═══════════════════════════════════════════════════════════════════════════
from app.utils.slug import slugify

class TestSlugify:
    def test_basic_string(self):
        assert slugify("Hola Mundo") == "hola-mundo"

    def test_removes_accents(self):
        assert slugify("Ácido Úrico") == "acido-urico"

    def test_removes_special_chars(self):
        assert slugify("Precio: $100!") == "precio-100"

    def test_collapses_spaces(self):
        assert slugify("a   b") == "a-b"

    def test_strips_leading_trailing_dashes(self):
        assert slugify("  hola  ") == "hola"

    def test_already_slug(self):
        assert slugify("hola-mundo") == "hola-mundo"

    def test_numbers_preserved(self):
        assert slugify("Producto 123") == "producto-123"

    def test_empty_string(self):
        assert slugify("") == ""

    def test_only_special_chars(self):
        assert slugify("!@#$%") == ""

    def test_eñe(self):
        # ñ → n
        assert slugify("Año Nuevo") == "ano-nuevo"

    def test_ü_becomes_u(self):
        assert slugify("Über") == "uber"

    def test_multiple_dashes_collapsed(self):
        assert slugify("a--b") == "a-b"

# ═══════════════════════════════════════════════════════════════════════════
# normalize_text
# ═══════════════════════════════════════════════════════════════════════════
from app.utils.normalize_text import normalize_text

class TestNormalizeText:
    def test_lowercases(self):
        assert normalize_text("HOLA") == "hola"

    def test_strips_whitespace(self):
        assert normalize_text("  hola  ") == "hola"

    def test_collapses_spaces(self):
        assert normalize_text("hola   mundo") == "hola mundo"

    def test_removes_accents(self):
        assert normalize_text("Ácido") == "acido"

    def test_none_returns_none(self):
        assert normalize_text(None) is None

    def test_empty_string(self):
        assert normalize_text("") == ""

# ═══════════════════════════════════════════════════════════════════════════
# formatters
# ═══════════════════════════════════════════════════════════════════════════
from app.utils.formatters import normalize_tax_id, normalize_email, normalize_phone

class TestNormalizeTaxId:
    def test_strips_non_digits(self):
        assert normalize_tax_id("30-12345678-9") == "30123456789"

    def test_none_returns_none(self):
        assert normalize_tax_id(None) is None

    def test_empty_returns_none(self):
        assert normalize_tax_id("") is None

    def test_already_clean(self):
        assert normalize_tax_id("12345678") == "12345678"

class TestNormalizeEmail:
    def test_lowercases(self):
        assert normalize_email("Test@EXAMPLE.COM") == "test@example.com"

    def test_strips_whitespace(self):
        assert normalize_email("  user@example.com  ") == "user@example.com"

    def test_none_returns_none(self):
        assert normalize_email(None) is None

    def test_empty_returns_none(self):
        assert normalize_email("") is None

class TestNormalizePhone:
    def test_strips_non_digits(self):
        assert normalize_phone("+54 3764 123456") == "543764123456"

    def test_removes_float_suffix(self):
        assert normalize_phone("3764123456.0") == "3764123456"

    def test_int_input(self):
        assert normalize_phone(3764123456) == "3764123456"

    def test_none_returns_none(self):
        assert normalize_phone(None) is None

    def test_empty_returns_none(self):
        assert normalize_phone("") is None

    def test_already_clean(self):
        assert normalize_phone("3764123456") == "3764123456"

# ═══════════════════════════════════════════════════════════════════════════
# geo
# ═══════════════════════════════════════════════════════════════════════════
from app.utils.geo import validate_coordinates, compute_h3, km_to_h3_k

class TestValidateCoordinates:
    def test_valid_coordinates(self):
        validate_coordinates(-27.3671, -55.8961)  # No exception

    def test_invalid_lat_too_high(self):
        with pytest.raises(ValueError, match="Latitud"):
            validate_coordinates(91, 0)

    def test_invalid_lat_too_low(self):
        with pytest.raises(ValueError, match="Latitud"):
            validate_coordinates(-91, 0)

    def test_invalid_lng_too_high(self):
        with pytest.raises(ValueError, match="Longitud"):
            validate_coordinates(0, 181)

    def test_invalid_lng_too_low(self):
        with pytest.raises(ValueError, match="Longitud"):
            validate_coordinates(0, -181)

    def test_boundary_lat_90(self):
        validate_coordinates(90, 0)  # No exception

    def test_boundary_lat_neg90(self):
        validate_coordinates(-90, 0)  # No exception

    def test_boundary_lng_180(self):
        validate_coordinates(0, 180)  # No exception

class TestComputeH3:
    def test_returns_string_for_valid_coords(self):
        result = compute_h3(-27.3671, -55.8961)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_none_none_returns_none(self):
        assert compute_h3(None, None) is None

    def test_mismatched_lat_lng_raises(self):
        with pytest.raises(ValueError, match="juntos"):
            compute_h3(-27.3671, None)

    def test_mismatched_lng_lat_raises(self):
        with pytest.raises(ValueError, match="juntos"):
            compute_h3(None, -55.8961)

    def test_same_coords_same_h3(self):
        h1 = compute_h3(-27.3671, -55.8961)
        h2 = compute_h3(-27.3671, -55.8961)
        assert h1 == h2

    def test_different_coords_may_differ(self):
        h1 = compute_h3(-27.3671, -55.8961)
        h2 = compute_h3(-34.6037, -58.3816)  # Buenos Aires
        assert h1 != h2

class TestKmToH3K:
    def test_returns_positive_int(self):
        k = km_to_h3_k(5)
        assert k >= 1

    def test_larger_radius_larger_k(self):
        assert km_to_h3_k(50) > km_to_h3_k(1)

    def test_zero_raises(self):
        with pytest.raises(ValueError):
            km_to_h3_k(0)

    def test_negative_raises(self):
        with pytest.raises(ValueError):
            km_to_h3_k(-5)