from datetime import date
from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_active_user
from app.core.rate_limit import limiter
from app.db.base import get_db_with_commit
from app.models.sales_rep_model import SalesRep
from app.schemas.account_ledger_import_schema import ClientImportResult, SupplierImportResult
from app.services.account_ledger_import_service import AccountLedgerImportService

router = APIRouter(prefix="/account-ledger/import", tags=["account-ledger-import"])


@router.post("/suppliers", response_model=SupplierImportResult)
@limiter.limit("10/minute")
def import_supplier_purchases(
    request: Request,
    file: UploadFile = File(...),
    sales_rep_id: int = Form(...),
    supplier_id: int = Form(...),
    purchase_date: date = Form(...),
    document_type: str = Form(default="purchase_invoice"),
    sheet_name: str | None = Form(default=None),
    dry_run: bool = Form(default=True),
    db: Session = Depends(get_db_with_commit),
    current_user: SalesRep = Depends(get_current_active_user),
):
    """
    Importa el bloque de pedido (columnas Pedido / Cantidad a comprar /
    Costo) de una hoja tipo Nico/Ariel/Guillermo. Con dry_run=true (default)
    solo previsualiza sin guardar nada. document_type ("purchase_invoice" o
    "purchase_quote") es el tipo POR DEFECTO: si la hoja trae una columna
    "document" (remito/invoice o presupuesto/quote), cada fila usa su valor y
    solo las filas con la celda vacía usan este default.
    """
    file_bytes = file.file.read()
    service = AccountLedgerImportService(db)
    return service.import_supplier_purchases(
        file_bytes=file_bytes,
        sheet_name=sheet_name,
        sales_rep_id=sales_rep_id,
        supplier_id=supplier_id,
        purchase_date=purchase_date,
        document_type=document_type,
        dry_run=dry_run,
        current_user=current_user,
    )


@router.post("/clients", response_model=ClientImportResult)
@limiter.limit("10/minute")
def import_client_sales(
    request: Request,
    file: UploadFile = File(...),
    sheet_name: str | None = Form(default=None),
    document_type: str = Form(default="sales_invoice"),
    dry_run: bool = Form(default=True),
    db: Session = Depends(get_db_with_commit),
    current_user: SalesRep = Depends(get_current_active_user),
):
    """
    Importa la hoja "Registro Clientes" (fecha, cliente, estado, importe,
    forma de pago). El cliente debe existir ya en el sistema (se matchea
    por nombre). Con dry_run=true (default) solo previsualiza.
    document_type ("sales_invoice" o "sales_quote") es el tipo POR DEFECTO de
    las ventas de cada vendedor. Si la hoja trae una columna "document"
    (remito/invoice o presupuesto/quote), cada fila usa su valor y solo las
    filas con la celda vacía usan este default. Un presupuesto queda
    'approved' y registra la misma deuda que uno generado por un pedido,
    pero no descuenta stock.
    """
    file_bytes = file.file.read()
    service = AccountLedgerImportService(db)
    return service.import_client_sales(
        file_bytes=file_bytes,
        sheet_name=sheet_name,
        document_type=document_type,
        dry_run=dry_run,
        current_user=current_user,
    )