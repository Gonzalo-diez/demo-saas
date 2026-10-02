from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict

# --- Resumen de deuda total ---

class AccountBalanceSummary(BaseModel):
    """
    Resumen agregado de saldos de TODOS los clientes o proveedores
    (no depende de filtros de página).

    Para clientes: `total_debt` = cuánto nos deben en total (deudores),
    `total_favor` = cuánto tenemos a favor de clientes (crédito a su favor).
    Para proveedores: `total_debt` = cuánto les debemos en total,
    `total_favor` = cuánto tenemos a nuestro favor con ellos.
    """
    total_debt: Decimal
    total_favor: Decimal
    net_balance: Decimal
    debtor_count: int
    favor_count: int

    model_config = ConfigDict(from_attributes=True)


# --- Antigüedad de deuda (aging) ---

class AccountAgingBucket(BaseModel):
    label: str
    min_days: int
    max_days: int | None
    amount: Decimal
    invoice_count: int


class AccountAgingSummary(BaseModel):
    buckets: list[AccountAgingBucket]
    total_pending: Decimal


# --- Ranking de mayores deudores / acreedores ---

class AccountRankingItem(BaseModel):
    id: int
    name: str
    balance: Decimal

    model_config = ConfigDict(from_attributes=True)


# --- Evolución del saldo en el tiempo ---

class AccountBalanceHistoryPoint(BaseModel):
    date: datetime
    balance: Decimal
    movement_type: str
    amount: Decimal

    model_config = ConfigDict(from_attributes=True)
