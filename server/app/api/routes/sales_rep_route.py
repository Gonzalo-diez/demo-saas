import io
from fastapi import APIRouter, Depends, File, Response, UploadFile, status, Request
from typing import Literal
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from sqlalchemy.orm import Session
from app.core.rate_limit import limiter
from app.core.auth_cookies import clear_auth_cookie, set_auth_cookie
from app.db.base import get_db, get_db_with_commit
from app.core.dependencies import (
    TenantRef,
    bind_tenant_from_ref,
    get_current_active_user,
    get_current_superuser,
    get_tenant_ref,
)
from app.models.sales_rep_model import SalesRep
from app.services.sales_rep_service import SalesRepService
from app.services.sales_rep_import_service import SalesRepImportService
from app.schemas.sales_rep_schema import (
    ChangePasswordRequest,
    MessageResponse,
    SalesRepCreate,
    SalesRepListResponse,
    SalesRepMapResponse,
    SalesRepLogin,
    SalesRepResponse,
    SalesRepUpdate,
)
from app.schemas.sales_rep_import_schema import (
    SalesRepImportCommitResponse,
    SalesRepImportPreviewResponse,
    SalesRepImportCommitRequest,
)

router = APIRouter(prefix="/sales-reps", tags=["SalesReps"])

@router.get("/", response_model=SalesRepListResponse)
@limiter.limit("30/minute")
def get_sales_reps(
    request: Request,
    page: int = 1,
    page_size: int = 20,
    search: str | None = None,
    status: str | None = None,
    sort: str | None = None,
    db: Session = Depends(get_db),
    _: SalesRep = Depends(get_current_active_user),
):
    service = SalesRepService(db)
    return service.get_sales_reps(
        page=page,
        page_size=page_size,
        search=search,
        status_filter=status,
        sort=sort,
    )

@router.get("/map", response_model=SalesRepMapResponse)
@limiter.limit("30/minute")
def get_sales_reps_for_map(
    request: Request,
    lat: float | None = None,
    lng: float | None = None,
    radius_km: float | None = None,
    search: str | None = None,
    is_active: bool | None = None,
    db: Session = Depends(get_db),
    _: SalesRep = Depends(get_current_active_user),
):
    service = SalesRepService(db)

    return service.get_sales_reps_for_map(
        lat=lat,
        lng=lng,
        radius_km=radius_km,
        search=search,
        is_active=is_active,
    )

@router.get("/me", response_model=SalesRepResponse)
def get_me(current_user: SalesRep = Depends(get_current_active_user)):
    return current_user

@router.post("/", response_model=SalesRepResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
def create_sales_rep(
    request: Request,
    data: SalesRepCreate,
    db: Session = Depends(get_db_with_commit),
    _: SalesRep = Depends(get_current_superuser),
):
    # El vendedor se crea siempre en el tenant del superusuario logueado
    # (la sesión ya está atada a él); el cliente no puede elegir otro.
    service = SalesRepService(db)
    return service.create(data)

@router.post("/login", response_model=SalesRepResponse)
@limiter.limit("5/minute")
def login_sales_rep(
    request: Request,
    data: SalesRepLogin,
    response: Response,
    db: Session = Depends(get_db_with_commit),
    tenant_ref: TenantRef = Depends(get_tenant_ref),
):
    # El email es único por distribuidora, no global: hay que saber a cuál entra.
    bind_tenant_from_ref(db, tenant_ref, data.tenant_slug)
    service = SalesRepService(db)
    sales_rep, access_token = service.login(data)
    set_auth_cookie(
        response,
        access_token,
    )
    return sales_rep

@router.post("/logout", response_model=MessageResponse)
@limiter.limit("5/minute")
def logout_sales_rep(
    request: Request,
    response: Response,
):
    clear_auth_cookie(response)
    return {"message": "Sesión cerrada correctamente"}

@router.get(
    "/import/sample-excel",
    summary="Descargar Excel de ejemplo para importar vendedores",
    response_class=Response,
    responses={
        200: {
            "content": {
                "application/vnd.openxmlformats-officedocument.spreadheetml.sheet": {}
            },
            "description": "Plantilla .xlsx lista para completar y subir a /import/preview.",
        }
    },
)
def download_sales_rep_import_sample(
    _: SalesRep = Depends(get_current_superuser),
):
    """
    Devuelve un archivo Excel de ejemplo explicando cómo preparar los datos
    para importar vendedores via **POST /api/clients/import/preview**.

    La hoja **'Vendedores'** incluye:
    - Encabezados coloreados (azul oscuro = obligatorio, azul claro = opcional).
    - Filas de ejemplo con datos reales.
    - Una hoja **'Instrucciones'** con el paso a paso completo del proceso.
    """
    
    required_fill = PatternFill("solid", fgColor="2E75B6")
    optional_fill = PatternFill("solid", fgColor="70A9D6")
    header_font   = Font(name="Arial", bold=True, color="FFFFFF", size=11)
    data_font     = Font(name="Arial", size=10)
    thin_border   = Border(
        left=Side(style="thin"), right=Side(style="thin"),
        top=Side(style="thin"),  bottom=Side(style="thin"),
    )
    red_font    = Font(name="Arial", bold=True, color="C00000", size=10)
    title_font  = Font(name="Arial", bold=True, size=13)
    step_font   = Font(name="Arial", bold=True, size=11)
    normal_font = Font(name="Arial", size=10)

    wb = openpyxl.Workbook()
    
    ws = wb.active
    ws.title = "Vendedores"
    ws.freeze_panes = "A2"
    
    columns = [
        ("name",               True,  36, "Nombre del vendedor"),
        ("email",              True,  32, "Email del vendedor"),
        ("password",           True,  36, "Contraseña del vendedor"),
        ("is_active",          False, 13, "TRUE o FALSE (default TRUE)"),
        ("is_superuser",       False, 13, "TRUE o FALSE (default FALSE)"),
        ("phone",              False, 24, "Teléfono del vendedor"),
        ("home_lat",           False, 13, "Latitud del domicilio (decimal). Ej: -27.3671"),
        ("home_lng",           False, 13, "Longitud del domicilio (decimal). Ej: -55.8961"),
        ("coverage_radius_km", False, 13, "Radio de cobertura en km. Ej: 10.5"),
    ]

    # ── Hoja 1: Vendedores ────────────────────────────────────────────────────
    for col_idx, (col_name, required, width, _) in enumerate(columns, start=1):
        cell = ws.cell(row=1, column=col_idx, value=col_name)
        cell.fill      = required_fill if required else optional_fill
        cell.font      = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border    = thin_border
        ws.column_dimensions[get_column_letter(col_idx)].width = width
    ws.row_dimensions[1].height = 42

    samples = [
        ["Juan Pérez",   "juan.perez@empresa.com",  "segura123", True,  False, "+54 3764 123456", -27.3671, -55.8961, 15.0],
        ["María Gómez",  "maria.gomez@empresa.com", "clave456",  True,  False, "+54 3764 654321", -27.3500, -55.8800, 20.0],
        ["Carlos López", "carlos.lopez@empresa.com","pass789",   True,  True,  None,              None,     None,     None],
    ]
    for r_idx, row in enumerate(samples, start=2):
        for c_idx, val in enumerate(row, start=1):
            cell = ws.cell(row=r_idx, column=c_idx, value=val)
            cell.font      = data_font
            cell.alignment = Alignment(vertical="center")
            cell.border    = thin_border
        ws.row_dimensions[r_idx].height = 18

    # Leyenda
    legend_row = len(samples) + 4
    ws.cell(row=legend_row, column=1, value="LEYENDA:").font = Font(name="Arial", bold=True, size=10)
    req_cell = ws.cell(row=legend_row + 1, column=1, value="  Azul oscuro = Campo OBLIGATORIO (no puede estar vacío)")
    req_cell.fill = required_fill
    req_cell.font = Font(name="Arial", color="FFFFFF", size=9)
    ws.merge_cells(start_row=legend_row + 1, start_column=1, end_row=legend_row + 1, end_column=5)
    opt_cell = ws.cell(row=legend_row + 2, column=1, value="  Azul claro  = Campo OPCIONAL (podés dejarlo vacío)")
    opt_cell.fill = optional_fill
    opt_cell.font = Font(name="Arial", color="FFFFFF", size=9)
    ws.merge_cells(start_row=legend_row + 2, start_column=1, end_row=legend_row + 2, end_column=5)

    # Advertencia
    warn_row = legend_row + 4
    warn_cell = ws.cell(
        row=warn_row, column=1,
        value="⚠  No elimines ni renombres los encabezados de la fila 1. "
              "No agregues columnas extra. Eliminá estas filas de ejemplo antes de subir el archivo real.",
    )
    warn_cell.font = red_font
    ws.merge_cells(start_row=warn_row, start_column=1, end_row=warn_row, end_column=len(columns))

    # ── Hoja 2: Instrucciones ────────────────────────────────────────────────
    wi = wb.create_sheet("Instrucciones")
    wi.column_dimensions["A"].width = 4
    wi.column_dimensions["B"].width = 90

    r = 1
    cell = wi.cell(row=r, column=1, value="📋  Cómo importar vendedores correctamente")
    cell.font = title_font
    wi.row_dimensions[r].height = 30
    wi.merge_cells(start_row=r, start_column=1, end_row=r, end_column=2)
    r += 2

    steps = [
        (
            "Paso 1 — Completá los datos en la hoja 'Vendedores'",
            [
                "• Completá una fila por vendedor.",
                "• Los campos en azul oscuro son OBLIGATORIOS: name, email y password.",
                "• Los campos en azul claro son opcionales.",
                "• home_lat, home_lng y coverage_radius_km deben venir los tres juntos (o todos vacíos).",
                "• Eliminá las filas de ejemplo antes de subir el archivo.",
            ],
        ),
        (
            "Paso 2 — Guardá el archivo como .xlsx",
            [
                "• Archivo > Guardar como > Formato: Excel (.xlsx).",
                "• No lo guardes como .csv ni .xls, solo .xlsx es aceptado.",
            ],
        ),
        (
            "Paso 3 — Subí el archivo a 'Vista Previa'",
            [
                "• Usá el endpoint POST /api/sales-reps/import/preview enviando el archivo.",
                "• El sistema te mostrará qué filas son válidas y cuáles tienen errores.",
                "• Las filas con errores NO se importan; podés corregirlas y volver a subir.",
            ],
        ),
        (
            "Paso 4 — Confirmá la importación",
            [
                "• Si el preview es correcto, usá POST /api/sales-reps/import/commit.",
                "• El modo por defecto es 'create': crea nuevos vendedores.",
                "• Con modo 'upsert': si el email ya existe, actualiza el registro existente.",
            ],
        ),
    ]

    for title, bullets in steps:
        title_cell = wi.cell(row=r, column=1, value=title)
        title_cell.font = step_font
        wi.row_dimensions[r].height = 22
        wi.merge_cells(start_row=r, start_column=1, end_row=r, end_column=2)
        r += 1
        for bullet in bullets:
            bc = wi.cell(row=r, column=2, value=bullet)
            bc.font = normal_font
            wi.row_dimensions[r].height = 16
            r += 1
        r += 1

    r += 1
    hdr = wi.cell(row=r, column=1, value="Reglas importantes por columna:")
    hdr.font = Font(name="Arial", bold=True, size=11)
    wi.merge_cells(start_row=r, start_column=1, end_row=r, end_column=2)
    r += 1

    rules = [
        ("name",               "OBLIGATORIO. Nombre completo del vendedor. Máx. 255 caracteres."),
        ("email",              "OBLIGATORIO. Email único del vendedor. Se usa como identificador en modo upsert."),
        ("password",           "OBLIGATORIO. Contraseña inicial del vendedor. Mín. 6 caracteres."),
        ("is_active",          "Opcional. TRUE o FALSE. Indica si el vendedor está activo. Default: TRUE."),
        ("is_superuser",       "Opcional. TRUE o FALSE. Otorga permisos de administrador. Default: FALSE."),
        ("phone",              "Opcional. Teléfono con código de país. Ej: +54 3764 123456."),
        ("home_lat",           "Opcional. Latitud del domicilio en decimal. Ej: -27.3671. Requiere home_lng y coverage_radius_km."),
        ("home_lng",           "Opcional. Longitud del domicilio en decimal. Ej: -55.8961. Requiere home_lat y coverage_radius_km."),
        ("coverage_radius_km", "Opcional. Radio de cobertura geográfica en km. Debe ser mayor a 0. Ej: 15.0."),
    ]
    for col_name, rule in rules:
        wi.cell(row=r, column=1, value=col_name).font = Font(name="Arial", bold=True, size=10)
        wi.cell(row=r, column=2, value=rule).font = normal_font
        wi.row_dimensions[r].height = 16
        r += 1

    # ── Serializar ───────────────────────────────────────────────────────────
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)

    return Response(
        content=buf.read(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=vendedores_importacion_ejemplo.xlsx"},
    )


@router.post("/import/preview", response_model=SalesRepImportPreviewResponse)
@limiter.limit("5/minute")
async def preview_sales_rep_import(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db_with_commit),
    _: SalesRep = Depends(get_current_superuser),
):
    import_service = SalesRepImportService(db)
    content = await file.read()
    return import_service.preview(content)

@router.post("/import/commit", response_model=SalesRepImportCommitResponse)
@limiter.limit("5/minute")
async def commit_sales_rep_import(
    request: Request,
    data: SalesRepImportCommitRequest,
    db: Session = Depends(get_db_with_commit),
    _: SalesRep = Depends(get_current_superuser)
):
    """
    Persiste los vendedores validados previamente en la base de datos.
    Soporta modo 'upsert' (crea o actualiza por username/email).
    """
    import_service = SalesRepImportService(db)
    return import_service.commit(data)

@router.post(
    "/import/commit-file",
    response_model=SalesRepImportCommitResponse,
)
@limiter.limit("5/minute")
async def commit_sales_rep_import_file(
    request: Request,
    file: UploadFile = File(...),
    mode: Literal["create", "upsert"] = "create",
    db: Session = Depends(get_db_with_commit),
    _: SalesRep = Depends(get_current_superuser),
):
    import_service = SalesRepImportService(db)

    content = await file.read()

    preview = import_service.preview(content)

    return import_service.commit(
        SalesRepImportCommitRequest(
            rows=preview.rows_valid,
            mode=mode,
        )
    )

@router.get("/{sales_rep_id}", response_model=SalesRepResponse)
def get_sales_rep(
    sales_rep_id: int,
    db: Session = Depends(get_db),
    _: SalesRep = Depends(get_current_active_user),
):
    service = SalesRepService(db)
    return service.get_by_id(sales_rep_id)

@router.patch("/{sales_rep_id}", response_model=SalesRepResponse)
@limiter.limit("5/minute")
def update_sales_rep(
    request: Request,
    sales_rep_id: int,
    data: SalesRepUpdate,
    db: Session = Depends(get_db_with_commit),
    _: SalesRep = Depends(get_current_superuser),
):
    service = SalesRepService(db)
    return service.update_by_id(sales_rep_id, data)

@router.patch("/{sales_rep_id}/change-password", response_model=MessageResponse)
@limiter.limit("5/minute")
def change_password(
    request: Request,
    sales_rep_id: int,
    data: ChangePasswordRequest,
    db: Session = Depends(get_db_with_commit),
    _: SalesRep = Depends(get_current_superuser),
):
    service = SalesRepService(db)
    service.update_password_by_id(sales_rep_id, data.new_password)
    return {"message": "Contraseña actualizada correctamente"}

@router.patch("/{sales_rep_id}/deactivate", response_model=SalesRepResponse)
@limiter.limit("5/minute")
def deactivate_sales_rep(
    request: Request,
    sales_rep_id: int,
    db: Session = Depends(get_db_with_commit),
    _: SalesRep = Depends(get_current_superuser),
):
    service = SalesRepService(db)
    return service.deactivate(sales_rep_id)

@router.patch("/{sales_rep_id}/activate", response_model=SalesRepResponse)
@limiter.limit("5/minute")
def activate_sales_rep(
    request: Request,
    sales_rep_id: int,
    db: Session = Depends(get_db_with_commit),
    _: SalesRep = Depends(get_current_superuser),
):
    service = SalesRepService(db)
    return service.activate(sales_rep_id)