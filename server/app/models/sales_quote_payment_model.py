from __future__ import annotations
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING
from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from app.models.mixin_model import TenantMixin

if TYPE_CHECKING:
    from app.models.sales_quote_model import SalesQuote
    from app.models.sales_rep_model import SalesRep

class SalesQuotePayment(Base, TenantMixin):
    __tablename__ = "sales_quote_payments"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    sales_quote_id: Mapped[int] = mapped_column(
        ForeignKey("sales_quotes.id"),
        nullable=False,
        index=True,
    )

    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    payment_method: Mapped[str] = mapped_column(String(30), nullable=False)
    # 'efectivo' | 'debito' | 'credito' | 'cheque' | 'otro'

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_by: Mapped[int | None] = mapped_column(
        ForeignKey("sales_reps.id"),
        nullable=True,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    sales_quote: Mapped["SalesQuote"] = relationship(
        "SalesQuote",
        back_populates="online_payments",
    )
    creator: Mapped["SalesRep | None"] = relationship("SalesRep")