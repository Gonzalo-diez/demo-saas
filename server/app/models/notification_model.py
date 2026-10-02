from __future__ import annotations
from datetime import datetime
from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from app.models.mixin_model import TenantMixin

class Notification(Base, TenantMixin):
    """
    Aviso interno para el personal (stock bajo / sin stock, cheques por
    vencer, etc.).

    Es un aviso de CONDICIÓN: hay a lo sumo UNA notificación activa
    (resolved_at IS NULL) por `dedup_key` (ej. "stock:15" o "check:7"). Cuando
    la condición cambia de gravedad se actualiza esa misma fila, y cuando
    desaparece (se repuso el stock, se acreditó el cheque) se marca como
    resuelta. Las que registran un hecho puntual (cheque rechazado) quedan
    activas hasta que se archivan con el tiempo.

    La visibilidad es general (todo el personal activo ve lo mismo); lo único
    que es por usuario es si la leyó o no (NotificationRead).
    """
    __tablename__ = "notifications"
    
    __table_args__ = (
        # Una sola notificación ACTIVA por dedup_key (las resueltas quedan de
        # historial y pueden repetirse).
        Index(
            "uq_notifications_tenant_active_dedup_key",
            "tenant_id",
            "dedup_key",
            unique=True,
            postgresql_where=text("resolved_at IS NULL"),
            sqlite_where=text("resolved_at IS NULL"),
        ),
        Index("ix_notifications_entity", "entity_type", "entity_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # 'stock' | 'check'
    category: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    # Ver NOTIFICATION_TYPE_META
    type: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    # 'info' | 'warning' | 'critical'
    severity: Mapped[str] = mapped_column(String(10), nullable=False)
    level: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)

    dedup_key: Mapped[str] = mapped_column(String(100), nullable=False)

    # A qué apunta: 'product' | 'check' (+ id), para que el frontend arme el link.
    entity_type: Mapped[str | None] = mapped_column(String(20), nullable=True)
    entity_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Última vez que se avisó (alta o escalada de gravedad); ordena el listado.
    notified_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    reads: Mapped[list["NotificationRead"]] = relationship(
        "NotificationRead",
        back_populates="notification",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class NotificationRead(Base):
    """Marca que un usuario (SalesRep) ya leyó una notificación."""
    __tablename__ = "notification_reads"

    notification_id: Mapped[int] = mapped_column(
        ForeignKey("notifications.id", ondelete="CASCADE"),
        primary_key=True,
    )
    sales_rep_id: Mapped[int] = mapped_column(
        ForeignKey("sales_reps.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
    )
    read_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    notification: Mapped["Notification"] = relationship(
        "Notification", back_populates="reads"
    )
