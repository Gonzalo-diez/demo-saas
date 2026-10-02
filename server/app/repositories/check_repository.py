from datetime import date
from decimal import Decimal
from typing import List, Optional, Tuple
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from app.models.check_model import Check


class CheckRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, check_id: int) -> Optional[Check]:
        return self.db.get(Check, check_id)

    def get_by_id_for_update(self, check_id: int) -> Optional[Check]:
        query = select(Check).where(Check.id == check_id).with_for_update()
        return self.db.scalar(query)

    def create(
        self,
        *,
        direction: str,
        check_number: str,
        bank_name: str | None,
        drawer_name: str | None,
        amount: Decimal,
        issue_date: date,
        payment_date: date,
        due_date: date,
        notes: str | None,
        client_id: int | None,
        supplier_id: int | None,
        pending_allocations: list | None,
        created_by: int | None,
    ) -> Check:
        check = Check(
            direction=direction,
            check_number=check_number,
            bank_name=bank_name,
            drawer_name=drawer_name,
            amount=amount,
            issue_date=issue_date,
            payment_date=payment_date,
            due_date=due_date,
            status="pendiente",
            notes=notes,
            client_id=client_id,
            supplier_id=supplier_id,
            pending_allocations=pending_allocations,
            created_by=created_by,
        )
        self.db.add(check)
        self.db.flush()
        self.db.refresh(check)
        return check

    def get_active_by_client(self, client_id: int) -> List[Check]:
        """Cheques recibidos de este cliente que todavía no se resolvieron
        (pendientes o depositados, pero no acreditados ni rechazados)."""
        query = (
            select(Check)
            .where(Check.client_id == client_id)
            .where(Check.status.in_(["pendiente", "depositado"]))
            .order_by(Check.payment_date.asc())
        )
        return list(self.db.scalars(query).all())

    def get_active_by_supplier(self, supplier_id: int) -> List[Check]:
        """Cheques emitidos a este proveedor que todavía no se resolvieron."""
        query = (
            select(Check)
            .where(Check.supplier_id == supplier_id)
            .where(Check.status.in_(["pendiente", "depositado"]))
            .order_by(Check.payment_date.asc())
        )
        return list(self.db.scalars(query).all())

    def get_checks(
        self,
        page: int = 1,
        page_size: int = 10,
        direction: Optional[str] = None,
        status_value: Optional[str] = None,
        client_id: Optional[int] = None,
        supplier_id: Optional[int] = None,
        due_before: Optional[date] = None,
    ) -> Tuple[List[Check], int]:
        query = select(Check)
        count_query = select(func.count()).select_from(Check)

        if direction:
            query = query.where(Check.direction == direction)
            count_query = count_query.where(Check.direction == direction)

        if status_value:
            query = query.where(Check.status == status_value)
            count_query = count_query.where(Check.status == status_value)

        if client_id:
            query = query.where(Check.client_id == client_id)
            count_query = count_query.where(Check.client_id == client_id)

        if supplier_id:
            query = query.where(Check.supplier_id == supplier_id)
            count_query = count_query.where(Check.supplier_id == supplier_id)

        if due_before:
            query = query.where(Check.due_date <= due_before)
            count_query = count_query.where(Check.due_date <= due_before)

        total = self.db.scalar(count_query) or 0

        query = (
            query.order_by(Check.due_date.asc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )

        checks = list(self.db.scalars(query).all())

        return checks, total