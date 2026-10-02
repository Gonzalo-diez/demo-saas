import io
import pandas as pd
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.repositories.product_repository import ProductRepository
from app.schemas.product_import_schema import (
    ProductImportPreviewResponse,
    ProductImportRow,
    ProductImportRowError,
    ProductImportCommitRequest,
    ProductImportCommitResponse,
)
from app.services.product_service import ProductService
 
 
def _sanitize_row(row_dict: dict) -> dict:
    """
    Convierte tipos numpy que pandas produce al leer Excel (np.int64, np.float64,
    np.bool_) a tipos Python nativos para que Pydantic los valide correctamente.
 
    Sin esto, filas válidas se rechazan en el preview porque Pydantic v2 no acepta
    escalares numpy directamente en todos los campos.
 
    Todos los escalares numpy implementan .item() que retorna el equivalente Python.
    Los tipos nativos (str, int, float, bool, None) pasan sin cambio.
    """
    clean = {}
    for key, val in row_dict.items():
        if val is None:
            clean[key] = None
        elif hasattr(val, "item"):
            clean[key] = val.item()
        else:
            clean[key] = val
    return clean
 
 
class ProductImportService:
    def __init__(self, db: Session):
        self.db = db
        self.product_repo = ProductRepository(db)
        self.product_service = ProductService(db)
 
    def preview(self, file_bytes: bytes) -> ProductImportPreviewResponse:
        """
        Lee el Excel y separa filas válidas de las que tienen errores de formato.
 
        Aplica _sanitize_row antes de validar para evitar que tipos numpy
        rechacen filas que son correctas en contenido.
        """
        try:
            df = pd.read_excel(io.BytesIO(file_bytes))
            df = df.where(pd.notnull(df), None)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error al leer Excel: {str(e)}")
 
        rows_valid   = []
        rows_invalid = []
 
        for index, row in df.iterrows():
            row_dict   = _sanitize_row(row.to_dict())
            row_number = index + 2  # +1 por índice 0, +1 por cabecera
 
            try:
                valid_row = ProductImportRow(**row_dict)
                rows_valid.append(valid_row)
            except Exception as e:
                errors = (
                    [f"{err['loc'][0]}: {err['msg']}" for err in e.errors()]
                    if hasattr(e, "errors")
                    else [str(e)]
                )
                rows_invalid.append(ProductImportRowError(
                    row_number=row_number,
                    data=row_dict,
                    errors=errors,
                ))
 
        return ProductImportPreviewResponse(
            total_rows=len(df),
            valid_rows=len(rows_valid),
            invalid_rows=len(rows_invalid),
            rows_valid=rows_valid,
            rows_invalid=rows_invalid,
        )
 
    def commit(self, data: ProductImportCommitRequest) -> ProductImportCommitResponse:
        """
        Delega la lógica de persistencia en ProductService.import_products_bulk,
        que es la implementación canónica (costo ponderado, movimientos de stock).
        Envuelve todo en try/except para reportar errores sin dejar la DB sucia.
        """
        total_to_process = len(data.rows)
        general_errors   = []
        result           = {"created": 0, "updated": 0}
 
        try:
            result = self.product_service.import_products_bulk(
                rows=data.rows,
                mode=data.mode,
            )
            self.db.flush()
        except Exception as e:
            self.db.rollback()
            general_errors.append(str(e))
 
        return ProductImportCommitResponse(
            total=total_to_process,
            created=result["created"],
            updated=result["updated"],
            failed=len(general_errors),
            errors=general_errors,
        )