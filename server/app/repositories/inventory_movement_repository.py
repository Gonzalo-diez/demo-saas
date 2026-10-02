from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload
from app.models.inventory_movement_model import InventoryMovement

class InventoryMovementRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, movement_id: int) -> InventoryMovement | None:
        stmt = (
            select(InventoryMovement)
            .options(
                joinedload(InventoryMovement.product),
                joinedload(InventoryMovement.creator),
            )
            .where(InventoryMovement.id == movement_id)
        )
        return self.db.scalar(stmt)

    def get_inventory_movements(
        self,
        page: int = 1,
        page_size: int = 20,
        product_id: int | None = None,
        movement_type: str | None = None,
        reference_type: str | None = None,
    ) -> tuple[list[InventoryMovement], int]:
        stmt = (
            select(InventoryMovement)
            .options(
                joinedload(InventoryMovement.product),
                joinedload(InventoryMovement.creator),
            )
            .order_by(InventoryMovement.id.desc())
        )

        count_stmt = select(func.count()).select_from(InventoryMovement)

        filters = []

        if product_id is not None:
            filters.append(InventoryMovement.product_id == product_id)

        if movement_type is not None:
            filters.append(InventoryMovement.movement_type == movement_type)

        if reference_type is not None:
            filters.append(InventoryMovement.reference_type == reference_type)

        if filters:
            stmt = stmt.where(*filters)
            count_stmt = count_stmt.where(*filters)

        stmt = stmt.offset((page - 1) * page_size).limit(page_size)

        items = list(self.db.scalars(stmt).all())
        total = self.db.scalar(count_stmt) or 0

        return items, total

    def create_without_commit(self, data: dict) -> InventoryMovement:
        movement = InventoryMovement(**data)
        self.db.add(movement)
        self.db.flush()
        self.db.refresh(movement)
        return movement