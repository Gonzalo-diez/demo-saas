from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    Response,
    status,
)
from sqlalchemy.orm import Session

from app.core.auth_cookies import (
    clear_auth_cookie,
    set_auth_cookie,
)
from app.core.config import settings
from app.core.dependencies import (
    get_current_platform_admin,
)
from app.core.rate_limit import limiter
from app.db.base import get_db
from app.models.admin_model import Admin
from app.schemas.admin_schema import (
    AdminCreate,
    AdminLogin,
    AdminResponse,
    AdminUpdate,
    MessageResponse,
)
from app.services.admin_service import AdminService


router = APIRouter(
    prefix="/admin",
    tags=["Platform Admin"],
)


@router.post(
    "/login",
    response_model=AdminResponse,
)
@limiter.limit("5/minute")
def login_admin(
    request: Request,
    data: AdminLogin,
    response: Response,
    db: Session = Depends(get_db),
):
    service = AdminService(db)

    admin, access_token = service.login(data)

    set_auth_cookie(
        response,
        access_token,
        cookie_name=settings.PLATFORM_AUTH_COOKIE_NAME,
    )

    return admin


@router.post(
    "/logout",
    response_model=MessageResponse,
)
@limiter.limit("5/minute")
def logout_admin(
    request: Request,
    response: Response,
):
    clear_auth_cookie(
        response,
        cookie_name=settings.PLATFORM_AUTH_COOKIE_NAME,
    )

    return {
        "message": "Sesión de administrador cerrada correctamente"
    }


@router.get(
    "/me",
    response_model=AdminResponse,
)
def get_admin_me(
    admin: Admin = Depends(
        get_current_platform_admin
    ),
):
    return admin

@router.get(
    "/users",
    response_model=list[AdminResponse],
)
def get_admins(
    db: Session = Depends(get_db),
    _: Admin = Depends(get_current_platform_admin),
):
    return AdminService(db).get_all()

@router.post(
    "/users",
    response_model=AdminResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_admin(
    data: AdminCreate,
    db: Session = Depends(get_db),
    _: Admin = Depends(get_current_platform_admin),
):
    return AdminService(db).create(data)


@router.patch(
    "/users/{admin_id}",
    response_model=AdminResponse,
)
def update_admin(
    admin_id: int,
    data: AdminUpdate,
    db: Session = Depends(get_db),
    current: Admin = Depends(get_current_platform_admin),
):
    if admin_id == current.id and data.is_active is False:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No podés desactivarte a vos mismo",
        )
    return AdminService(db).update(admin_id, data)


@router.delete(
    "/users/{admin_id}",
    response_model=MessageResponse,
)
def delete_admin(
    admin_id: int,
    db: Session = Depends(get_db),
    current: Admin = Depends(get_current_platform_admin),
):
    if admin_id == current.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No podés eliminarte a vos mismo",
        )
    AdminService(db).delete(admin_id)
    return {"message": "Administrador eliminado correctamente"}
