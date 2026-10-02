"""
test_import_services.py — Tests del servicio de importación de productos.
Genera Excel en memoria para probar el flujo de preview sin BD real.
"""
import io
import pytest
import openpyxl
from unittest.mock import MagicMock, patch


def _make_product_excel(rows: list[dict]) -> bytes:
    """Crea un Excel con las columnas esperadas por ProductImportService."""
    wb = openpyxl.Workbook()
    ws = wb.active
    headers = ["sku", "name", "brand", "category", "unit_cost", "unit_price",
               "stock_current", "stock_min", "description", "image_url", "is_active"]
    ws.append(headers)
    for row in rows:
        ws.append([row.get(h) for h in headers])
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


class TestProductImportServicePreview:
    def _make_service(self):
        from app.services.product_import_service import ProductImportService
        db = MagicMock()
        with patch("app.services.product_import_service.ProductRepository"), \
             patch("app.services.product_import_service.ProductService"):
            svc = ProductImportService(db)
        return svc

    def test_valid_rows_parsed(self):
        svc = self._make_service()
        excel = _make_product_excel([{
            "sku": "SKU-001",
            "name": "Aceite Test",
            "brand": "Marca",
            "category": "pilas",
            "unit_cost": 100.0,
            "unit_price": 150.0,
            "stock_current": 10,
            "stock_min": 2,
            "description": "Desc",  # string, no None/NaN
            "image_url": "https://img.com/x.jpg",
            "is_active": True,
        }])
        result = svc.preview(excel)
        assert len(result.rows_valid) == 1
        assert len(result.rows_invalid) == 0
        assert result.rows_valid[0].sku == "SKU-001"

    def test_invalid_row_missing_name(self):
        svc = self._make_service()
        excel = _make_product_excel([{
            "sku": "SKU-002",
            "name": None,  # requerido
            "brand": "Marca",
            "category": "pilas",
            "unit_cost": 100.0,
            "unit_price": 150.0,
            "stock_current": 0,
            "stock_min": 0,
            "description": None,
            "image_url": None,
            "is_active": True,
        }])
        result = svc.preview(excel)
        assert len(result.rows_valid) == 0
        assert len(result.rows_invalid) == 1

    def test_mixed_valid_and_invalid_rows(self):
        svc = self._make_service()
        excel = _make_product_excel([
            {
                "sku": "SKU-003", "name": "Válido", "brand": "M",
                "category": "pilas", "unit_cost": 50.0, "unit_price": 80.0,
                "stock_current": 5, "stock_min": 1, "description": "ok",
                "image_url": "https://img.com/x.jpg", "is_active": True,
            },
            {
                # Fila inválida: unit_cost negativo + name ausente
                "sku": "SKU-ERR", "name": None, "brand": "M",
                "category": "pilas", "unit_cost": -5.0, "unit_price": 80.0,
                "stock_current": 0, "stock_min": 0, "description": None,
                "image_url": None, "is_active": True,
            },
        ])
        result = svc.preview(excel)
        assert len(result.rows_valid) >= 1   # al menos la primera fila válida
        assert result.total_rows == 2

    def test_empty_excel_returns_empty(self):
        svc = self._make_service()
        excel = _make_product_excel([])
        result = svc.preview(excel)
        assert result.rows_valid == []
        assert result.rows_invalid == []

    def test_invalid_bytes_raises_http_error(self):
        from fastapi import HTTPException
        svc = self._make_service()
        with pytest.raises(HTTPException) as exc:
            svc.preview(b"not an excel file at all")
        assert exc.value.status_code == 400

    def test_negative_price_invalid(self):
        svc = self._make_service()
        excel = _make_product_excel([{
            "sku": "SKU-004",
            "name": "Prod",
            "brand": "Marca",
            "category": "pilas",
            "unit_cost": -1.0,  # negativo → inválido
            "unit_price": 50.0,
            "stock_current": 0,
            "stock_min": 0,
            "description": None,
            "image_url": None,
            "is_active": True,
        }])
        result = svc.preview(excel)
        assert len(result.rows_invalid) == 1


class TestProductImportServiceSanitizeRow:
    """Tests de la función _sanitize_row (conversión de tipos numpy)."""

    def test_sanitize_numpy_types(self):
        import numpy as np
        from app.services.product_import_service import _sanitize_row

        row = {
            "sku": np.str_("SKU-001"),
            "unit_cost": np.float64(100.5),
            "stock_current": np.int64(10),
            "is_active": np.bool_(True),
            "description": None,
        }
        result = _sanitize_row(row)
        assert isinstance(result["unit_cost"], float)
        assert isinstance(result["stock_current"], int)
        assert isinstance(result["is_active"], bool)
        assert result["description"] is None

    def test_sanitize_native_types_unchanged(self):
        from app.services.product_import_service import _sanitize_row

        row = {"name": "Test", "cost": 10.5, "active": True, "empty": None}
        result = _sanitize_row(row)
        assert result == row