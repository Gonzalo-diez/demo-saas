from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.sales_quote_payment_model import SalesQuotePayment


class SalesQuotePaymentRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_without_commit(self, data: dict) -> SalesQuotePayment:
        payment = SalesQuotePayment(**data)
        self.db.add(payment)
        self.db.flush()
        self.db.refresh(payment)
        return payment

    def get_by_quote_id(
        self,
        sales_quote_id: int,
    ) -> list[SalesQuotePayment]:
        stmt = (
            select(SalesQuotePayment)
            .options(joinedload(SalesQuotePayment.creator))
            .where(
                SalesQuotePayment.sales_quote_id == sales_quote_id
            )
            .order_by(SalesQuotePayment.id.desc())
        )

        return list(self.db.scalars(stmt).all())