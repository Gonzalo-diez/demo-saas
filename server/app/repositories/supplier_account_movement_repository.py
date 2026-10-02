from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload, selectinload
from app.models.supplier_account_movement_model import SupplierAccountMovement
from app.models.supplier_payment_allocation_model import SupplierPaymentAllocation

class SupplierAccountMovementRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, movement_id: int) -> SupplierAccountMovement | None:
        stmt = (
            select(SupplierAccountMovement)
            .options(
                joinedload(SupplierAccountMovement.supplier),
                joinedload(SupplierAccountMovement.creator),
                selectinload(SupplierAccountMovement.allocations).joinedload(
                    SupplierPaymentAllocation.purchase_invoice
                ),
            )
            .where(SupplierAccountMovement.id == movement_id)
        )
        return self.db.scalar(stmt)

    def get_movements(
        self,
        page: int = 1,
        page_size: int = 20,
        supplier_id: int | None = None,
        movement_type: str | None = None,
        reference_type: str | None = None,
    ) -> tuple[list[SupplierAccountMovement], int]:
        stmt = (
            select(SupplierAccountMovement)
            .options(
                joinedload(SupplierAccountMovement.supplier),
                joinedload(SupplierAccountMovement.creator),
                selectinload(SupplierAccountMovement.allocations).joinedload(
                    SupplierPaymentAllocation.purchase_invoice
                ),
            )
            .order_by(SupplierAccountMovement.id.desc())
        )

        count_stmt = select(func.count()).select_from(SupplierAccountMovement)

        filters = []

        if supplier_id is not None:
            filters.append(SupplierAccountMovement.supplier_id == supplier_id)

        if movement_type is not None:
            filters.append(SupplierAccountMovement.movement_type == movement_type)

        if reference_type is not None:
            filters.append(SupplierAccountMovement.reference_type == reference_type)

        if filters:
            stmt = stmt.where(*filters)
            count_stmt = count_stmt.where(*filters)

        stmt = stmt.offset((page - 1) * page_size).limit(page_size)

        items = list(self.db.scalars(stmt).all())
        total = self.db.scalar(count_stmt) or 0

        return items, total

    def get_balance_history(
        self,
        supplier_id: int,
        limit: int = 60,
    ) -> list[SupplierAccountMovement]:
        """
        Últimos `limit` movimientos del proveedor en orden cronológico
        ascendente, para graficar la evolución de balance_after en el tiempo.
        """
        stmt = (
            select(SupplierAccountMovement)
            .where(SupplierAccountMovement.supplier_id == supplier_id)
            .order_by(SupplierAccountMovement.created_at.desc())
            .limit(limit)
        )
        items = list(self.db.scalars(stmt).all())
        items.reverse()
        return items

    def create_without_commit(self, data: dict) -> SupplierAccountMovement:
        movement = SupplierAccountMovement(**data)
        self.db.add(movement)
        self.db.flush()
        self.db.refresh(movement)
        return movement
