from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.repositories.supplier_repository import SupplierRepository
from app.schemas.supplier_schema import (
    SupplierCreate,
    SupplierUpdate,
)

class SupplierService:
    def __init__(self, db: Session):
        self.db = db
        self.supplier_repo = SupplierRepository(db)

    def create(self, data: SupplierCreate):
        if data.tax_id:
            existing_by_tax_id = self.supplier_repo.get_by_tax_id(data.tax_id)
            if existing_by_tax_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Ya existe un proveedor con ese tax_id",
                )

        existing_by_name = self.supplier_repo.get_by_name(data.name)
        if existing_by_name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ya existe un proveedor con ese nombre",
            )

        return self.supplier_repo.create(data)

    def get_suppliers(
        self,
        page: int = 1,
        page_size: int = 20,
        is_active: bool | None = None,
        search: str | None = None,
    ):
        if page < 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="page debe ser mayor o igual a 1",
            )

        if page_size < 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="page_size debe ser mayor o igual a 1",
            )

        suppliers, total = self.supplier_repo.get_suppliers(
            page=page,
            page_size=page_size,
            is_active=is_active,
            search=search,
        )

        total_pages = (total + page_size - 1) // page_size if total > 0 else 1

        return {
            "suppliers": suppliers,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        }

    def get_by_id(self, supplier_id: int):
        supplier = self.supplier_repo.get_by_id(supplier_id)
        if not supplier:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Proveedor no encontrado",
            )
        return supplier

    def update(self, supplier_id: int, data: SupplierUpdate):
        supplier = self.supplier_repo.get_by_id(supplier_id)
        if not supplier:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Proveedor no encontrado",
            )

        if data.tax_id:
            existing_by_tax_id = self.supplier_repo.get_by_tax_id(data.tax_id)
            if existing_by_tax_id and existing_by_tax_id.id != supplier.id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Ya existe otro proveedor con ese tax_id",
                )

        if data.name:
            existing_by_name = self.supplier_repo.get_by_name(data.name)
            if existing_by_name and existing_by_name.id != supplier.id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Ya existe otro proveedor con ese nombre",
                )

        return self.supplier_repo.update(supplier, data)

    def deactivate(self, supplier_id: int):
        supplier = self.supplier_repo.get_by_id(supplier_id)
        if not supplier:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Proveedor no encontrado",
            )

        update_data = SupplierUpdate(is_active=False)
        return self.supplier_repo.update(supplier, update_data)
    
    def activate(self, supplier_id: int):
        supplier = self.supplier_repo.get_by_id(supplier_id)
        if not supplier:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Proveedor no encontrado",
            )
            
        update_data = SupplierUpdate(is_active=True)
        return self.supplier_repo.update(supplier, update_data)