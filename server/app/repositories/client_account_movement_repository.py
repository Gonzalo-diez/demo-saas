from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload, selectinload
from app.models.client_account_movement_model import ClientAccountMovement
from app.models.client_payment_allocation_model import ClientPaymentAllocation

class ClientAccountMovementRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, movement_id: int) -> ClientAccountMovement | None:
        stmt = (
            select(ClientAccountMovement)
            .options(
                joinedload(ClientAccountMovement.client),
                joinedload(ClientAccountMovement.creator),
                selectinload(ClientAccountMovement.allocations).joinedload(
                    ClientPaymentAllocation.sales_invoice
                ),
                selectinload(ClientAccountMovement.allocations).joinedload(
                    ClientPaymentAllocation.sales_quote
                ),
            )
            .where(ClientAccountMovement.id == movement_id)
        )
        return self.db.scalar(stmt)

    def get_movements(
        self,
        page: int = 1,
        page_size: int = 20,
        client_id: int | None = None,
        movement_type: str | None = None,
        reference_type: str | None = None,
    ) -> tuple[list[ClientAccountMovement], int]:
        stmt = (
            select(ClientAccountMovement)
            .options(
                joinedload(ClientAccountMovement.client),
                joinedload(ClientAccountMovement.creator),
                selectinload(ClientAccountMovement.allocations).joinedload(
                    ClientPaymentAllocation.sales_invoice
                ),
                selectinload(ClientAccountMovement.allocations).joinedload(
                    ClientPaymentAllocation.sales_quote
                ),
            )
            .order_by(ClientAccountMovement.id.desc())
        )

        count_stmt = select(func.count()).select_from(ClientAccountMovement)

        filters = []

        if client_id is not None:
            filters.append(ClientAccountMovement.client_id == client_id)

        if movement_type is not None:
            filters.append(ClientAccountMovement.movement_type == movement_type)

        if reference_type is not None:
            filters.append(ClientAccountMovement.reference_type == reference_type)

        if filters:
            stmt = stmt.where(*filters)
            count_stmt = count_stmt.where(*filters)

        stmt = stmt.offset((page - 1) * page_size).limit(page_size)

        items = list(self.db.scalars(stmt).all())
        total = self.db.scalar(count_stmt) or 0

        return items, total

    def get_balance_history(
        self,
        client_id: int,
        limit: int = 60,
    ) -> list[ClientAccountMovement]:
        """
        Últimos `limit` movimientos del cliente en orden cronológico
        ascendente, para graficar la evolución de balance_after en el tiempo.
        """
        stmt = (
            select(ClientAccountMovement)
            .where(ClientAccountMovement.client_id == client_id)
            .order_by(ClientAccountMovement.created_at.desc())
            .limit(limit)
        )
        items = list(self.db.scalars(stmt).all())
        items.reverse()
        return items

    def create_without_commit(self, data: dict) -> ClientAccountMovement:
        movement = ClientAccountMovement(**data)
        self.db.add(movement)
        self.db.flush()
        self.db.refresh(movement)
        return movement
