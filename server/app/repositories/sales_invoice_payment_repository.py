from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload
from app.models.sales_invoice_payment_model import SalesInvoicePayment

class SalesInvoicePaymentRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_without_commit(self, data: dict) -> SalesInvoicePayment:
        payment = SalesInvoicePayment(**data)
        self.db.add(payment)
        self.db.flush()
        self.db.refresh(payment)
        return payment

    def get_by_invoice_id(self, sales_invoice_id: int) -> list[SalesInvoicePayment]:
        stmt = (
            select(SalesInvoicePayment)
            .options(joinedload(SalesInvoicePayment.creator))
            .where(SalesInvoicePayment.sales_invoice_id == sales_invoice_id)
            .order_by(SalesInvoicePayment.id.desc())
        )
        return list(self.db.scalars(stmt).all())
