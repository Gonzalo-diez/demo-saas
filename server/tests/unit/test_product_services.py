"""
test_product_service.py — Tests del ProductService con repositorio mockeado.
No requiere BD real.
"""
import pytest
from decimal import Decimal
from unittest.mock import MagicMock, patch

from fastapi import HTTPException


class TestProductServiceHelpers:
    """Tests de métodos estáticos/privados del servicio."""

    def _make_service(self):
        from app.services.product_service import ProductService
        db = MagicMock()
        with patch("app.services.product_service.ProductRepository"), \
             patch("app.services.product_service.InventoryMovementRepository"), \
             patch("app.services.product_service.InventoryMovementService"):
            svc = ProductService(db)
        return svc

    # ── _has_valid_image ───────────────────────────────────────────────────

    def test_valid_image_url(self):
        svc = self._make_service()
        assert svc._has_valid_image("https://example.com/img.jpg") is True

    def test_none_image(self):
        svc = self._make_service()
        assert svc._has_valid_image(None) is False

    def test_empty_image(self):
        svc = self._make_service()
        assert svc._has_valid_image("") is False

    @pytest.mark.parametrize("bad", ["nan", "none", "null", "n/a", "-", "NaN", "NONE"])
    def test_invalid_sentinel_values(self, bad):
        svc = self._make_service()
        assert svc._has_valid_image(bad) is False

    # ── _is_product_complete ───────────────────────────────────────────────

    def test_complete_product(self):
        svc = self._make_service()
        data = {
            "name": "Producto X",
            "brand": "Marca",
            "category": "pilas",
            "image_url": "https://img.com/x.jpg",
        }
        assert svc._is_product_complete(data) is True

    def test_missing_name(self):
        svc = self._make_service()
        data = {"name": "", "brand": "Marca", "category": "pilas", "image_url": "https://img.com/x.jpg"}
        assert svc._is_product_complete(data) is False

    def test_invalid_brand_pendiente(self):
        svc = self._make_service()
        data = {"name": "X", "brand": "pendiente", "category": "pilas", "image_url": "https://img.com/x.jpg"}
        assert svc._is_product_complete(data) is False

    def test_invalid_category_sin_clasificar(self):
        svc = self._make_service()
        data = {"name": "X", "brand": "Marca", "category": "sin clasificar", "image_url": "https://img.com/x.jpg"}
        assert svc._is_product_complete(data) is False

    def test_no_image_makes_incomplete(self):
        svc = self._make_service()
        data = {"name": "X", "brand": "Marca", "category": "pilas", "image_url": None}
        assert svc._is_product_complete(data) is False

    # ── _determine_product_state_import ───────────────────────────────────

    def test_active_state_with_image(self):
        svc = self._make_service()
        data = {"image_url": "https://img.com/x.jpg", "category": "pilas"}
        is_active, status = svc._determine_product_state_import(data)
        assert is_active is True
        assert status == "ACTIVE"

    def test_draft_state_without_image(self):
        svc = self._make_service()
        data = {"image_url": None, "category": "pilas"}
        is_active, status = svc._determine_product_state_import(data)
        assert is_active is False
        assert status == "DRAFT"

    def test_draft_state_sin_clasificar(self):
        svc = self._make_service()
        data = {"image_url": "https://img.com/x.jpg", "category": "sin clasificar"}
        is_active, status = svc._determine_product_state_import(data)
        assert is_active is False
        assert status == "DRAFT"

    # ── categorías libres/no-catálogo (venta B2B, no exigen imagen) ───────

    def test_complete_without_image_when_category_is_free(self):
        svc = self._make_service()
        data = {
            "name": "Repuesto interno",
            "brand": "Marca",
            "category": "Repuestos Vending",  # no está en la whitelist
            "image_url": None,
        }
        assert svc._is_product_complete(data) is True

    def test_still_needs_image_when_category_is_catalog(self):
        svc = self._make_service()
        data = {
            "name": "Producto catálogo",
            "brand": "Marca",
            "category": "pilas",  # sí está en la whitelist
            "image_url": None,
        }
        assert svc._is_product_complete(data) is False

    def test_import_active_without_image_when_category_is_free(self):
        svc = self._make_service()
        data = {"image_url": None, "category": "Repuestos Vending"}
        is_active, status = svc._determine_product_state_import(data)
        assert is_active is True
        assert status == "ACTIVE"

    def test_import_still_needs_image_when_category_is_catalog(self):
        svc = self._make_service()
        data = {"image_url": None, "category": "pilas"}
        is_active, status = svc._determine_product_state_import(data)
        assert is_active is False
        assert status == "DRAFT"


class TestProductServiceGetProduct:
    """Tests del método get_product."""

    def _make_service_with_repo(self, product=None):
        from app.services.product_service import ProductService
        db = MagicMock()
        with patch("app.services.product_service.ProductRepository") as MockRepo, \
             patch("app.services.product_service.InventoryMovementRepository"), \
             patch("app.services.product_service.InventoryMovementService"):
            svc = ProductService(db)
            svc.repo = MockRepo.return_value
            svc.repo.get_product_by_id.return_value = product
        return svc

    def test_get_product_not_found_raises_404(self):
        svc = self._make_service_with_repo(product=None)
        with pytest.raises(HTTPException) as exc:
            svc._get_product_or_404(999)
        assert exc.value.status_code == 404

    def test_get_product_found(self):
        mock_product = MagicMock()
        mock_product.id = 1
        svc = self._make_service_with_repo(product=mock_product)
        result = svc._get_product_or_404(1)
        assert result.id == 1