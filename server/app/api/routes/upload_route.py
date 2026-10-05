from fastapi import APIRouter, Depends, File, UploadFile, Request
from app.core.rate_limit import limiter
from app.core.dependencies import get_current_superuser
from app.models.sales_rep_model import SalesRep
from app.services.upload_service import upload_product_image

router = APIRouter(prefix="/upload", tags=["uploads"])

@router.post("/product-image")
@limiter.limit("5/minute")
async def upload_image(
    request: Request,
    file: UploadFile = File(...),
    current_user: SalesRep = Depends(get_current_superuser),
):
    # Cada distribuidora sube a su propia carpeta de Cloudinary.
    return await upload_product_image(file, tenant_id=current_user.tenant_id)


@router.post("/category-image")
@limiter.limit("5/minute")
async def upload_category_image(
    request: Request,
    file: UploadFile = File(...),
    current_user: SalesRep = Depends(get_current_superuser),
):
    """Sube la imagen de una categoría; la URL devuelta va en `image_url` de la categoría."""
    return await upload_product_image(
        file, tenant_id=current_user.tenant_id, subfolder="categorias"
    )