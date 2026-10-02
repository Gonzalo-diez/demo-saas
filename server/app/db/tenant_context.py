"""
Aislamiento multi-tenant a nivel de sesión de SQLAlchemy.

Idea: cada Session lleva el tenant "activo" en `session.info`. Con eso:

1. LECTURAS / UPDATE / DELETE: a toda sentencia que toque un modelo con
   TenantMixin se le agrega `WHERE tenant_id = <tenant activo>`
   (with_loader_criteria). Incluye subqueries, joins, lazy loads y
   `session.get()`. Los repositories no necesitan acordarse del filtro.
2. INSERT: antes del flush, todo objeto nuevo con TenantMixin y sin
   tenant_id recibe el del tenant activo. Si trae uno distinto → error.
3. FAIL-CLOSED: si la sesión no tiene tenant, las consultas devuelven
   vacío (nunca "todo") y los inserts fallan con un error claro.

Código de sistema (migraciones de datos, scripts, listado de tenants en
los jobs) puede usar `unscoped(db)` para saltear el filtro de forma
explícita y visible.

Limitación: las sentencias con `text()` o Core puro sobre `Model.__table__`
NO pasan por este filtro; hay que filtrar a mano con `require_tenant_id(db)`.
"""
from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

from sqlalchemy import event
from sqlalchemy import inspect as sa_inspect
from sqlalchemy.orm import Session, with_loader_criteria

from app.db.mixins import TenantMixin

TENANT_KEY = "tenant_id"
UNSCOPED_KEY = "tenant_unscoped"

# Valor imposible: si la sesión no tiene tenant, el filtro no matchea nada.
_NO_TENANT = -1


class TenantContextError(RuntimeError):
    """Se intentó escribir datos de un tenant sin saber de cuál."""


# ----------------------------------------------------------------------
# API pública
# ----------------------------------------------------------------------

def set_tenant(db: Session, tenant_id: int) -> None:
    db.info[TENANT_KEY] = int(tenant_id)


def get_tenant_id(db: Session) -> int | None:
    return db.info.get(TENANT_KEY)


def require_tenant_id(db: Session) -> int:
    tenant_id = get_tenant_id(db)
    if tenant_id is None:
        raise TenantContextError("La sesión no tiene un tenant activo.")
    return tenant_id


@contextmanager
def unscoped(db: Session) -> Iterator[Session]:
    """Desactiva el filtro por tenant dentro del bloque (uso de sistema)."""
    previous = db.info.get(UNSCOPED_KEY, False)
    db.info[UNSCOPED_KEY] = True
    try:
        yield db
    finally:
        db.info[UNSCOPED_KEY] = previous


@contextmanager
def tenant_scope(db: Session, tenant_id: int) -> Iterator[Session]:
    """Fija temporalmente el tenant de la sesión (jobs, scripts, tests)."""
    previous = db.info.get(TENANT_KEY)
    set_tenant(db, tenant_id)
    try:
        yield db
    finally:
        if previous is None:
            db.info.pop(TENANT_KEY, None)
        else:
            db.info[TENANT_KEY] = previous


# ----------------------------------------------------------------------
# Eventos globales sobre Session
# ----------------------------------------------------------------------

@event.listens_for(Session, "do_orm_execute")
def _apply_tenant_filter(state) -> None:
    if state.is_column_load:
        return
    if not (state.is_select or state.is_update or state.is_delete):
        return

    info = state.session.info
    if info.get(UNSCOPED_KEY):
        return

    tenant_id = info.get(TENANT_KEY)
    criteria_value = _NO_TENANT if tenant_id is None else int(tenant_id)

    state.statement = state.statement.options(
        with_loader_criteria(
            TenantMixin,
            lambda cls: cls.tenant_id == criteria_value,
            include_aliases=True,
        )
    )


@event.listens_for(Session, "before_flush")
def _stamp_and_guard_tenant(session: Session, flush_context, instances) -> None:
    info = session.info
    unscoped_session = bool(info.get(UNSCOPED_KEY))
    tenant_id = info.get(TENANT_KEY)

    for obj in session.new:
        if not isinstance(obj, TenantMixin):
            continue

        if obj.tenant_id is None:
            if tenant_id is None:
                raise TenantContextError(
                    f"No se puede crear {type(obj).__name__} sin tenant: "
                    "la sesión no tiene tenant activo."
                )
            obj.tenant_id = tenant_id
        elif (
            not unscoped_session
            and tenant_id is not None
            and obj.tenant_id != tenant_id
        ):
            raise TenantContextError(
                f"{type(obj).__name__} con tenant_id={obj.tenant_id} no puede "
                f"guardarse en una sesión del tenant {tenant_id}."
            )

    if unscoped_session:
        return

    for obj in session.dirty:
        if not isinstance(obj, TenantMixin):
            continue
        history = sa_inspect(obj).attrs.tenant_id.history
        if history.has_changes() and history.deleted and history.deleted[0] is not None:
            raise TenantContextError(
                f"No se puede cambiar el tenant de un {type(obj).__name__} existente."
            )
