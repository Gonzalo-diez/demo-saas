from sqlalchemy import case, select, func
from sqlalchemy.orm import Session
from app.models.supplier_model import Supplier
from app.schemas.supplier_schema import SupplierCreate, SupplierUpdate
from app.utils.formatters import normalize_tax_id

class SupplierRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, data: SupplierCreate) -> Supplier:
        payload = data.model_dump()

        payload["tax_id"] = normalize_tax_id(payload.get("tax_id"))

        supplier = Supplier(**payload)
        self.db.add(supplier)
        self.db.flush()
        self.db.refresh(supplier)
        return supplier
    
    def create_no_commit(
        self,
        data: SupplierCreate,
    ) -> Supplier:
        payload = data.model_dump()

        payload["tax_id"] = normalize_tax_id(
            payload.get("tax_id")
        )

        supplier = Supplier(**payload)

        self.db.add(supplier)
        self.db.flush()

        return supplier

    def get_by_id(self, supplier_id: int) -> Supplier | None:
        stmt = select(Supplier).where(Supplier.id == supplier_id)
        return self.db.scalar(stmt)

    def get_by_tax_id(self, tax_id: str) -> Supplier | None:
        normalized_tax_id = normalize_tax_id(tax_id)
        stmt = select(Supplier).where(Supplier.tax_id == normalized_tax_id)
        return self.db.scalar(stmt)

    def get_by_name(
        self,
        name: str,
    ) -> Supplier | None:
        normalized_name = "".join(
            name.strip().lower().split()
        )

        stmt = select(Supplier).where(
            func.replace(
                func.lower(Supplier.name),
                " ",
                "",
            )
            == normalized_name
        )

        return self.db.scalar(stmt)

    def get_suppliers(
        self,
        page: int = 1,
        page_size: int = 20,
        is_active: bool | None = None,
        search: str | None = None,
    ) -> tuple[list[Supplier], int]:
        query = self.db.query(Supplier)

        if is_active is not None:
            query = query.filter(Supplier.is_active == is_active)

        if search:
            search_term = f"%{search.strip()}%"
            query = query.filter(Supplier.name.ilike(search_term))

        total = query.count()

        suppliers = (
            query.order_by(Supplier.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )

        return suppliers, total

    def update(self, supplier: Supplier, data: SupplierUpdate) -> Supplier:
        update_data = data.model_dump(exclude_unset=True)
        
        if "tax_id" in update_data:
            update_data["tax_id"] = normalize_tax_id(update_data["tax_id"])

        for field, value in update_data.items():
            setattr(supplier, field, value)

        self.db.flush()
        self.db.refresh(supplier)
        return supplier
    
    def update_no_commit(
        self,
        supplier: Supplier,
        data: SupplierUpdate,
    ) -> Supplier:
        update_data = data.model_dump(
            exclude_unset=True
        )

        if "tax_id" in update_data:
            update_data["tax_id"] = normalize_tax_id(
                update_data["tax_id"]
            )

        for field, value in update_data.items():
            setattr(
                supplier,
                field,
                value,
            )

        self.db.flush()

        return supplier

    def delete(self, supplier: Supplier) -> None:
        self.db.delete(supplier)
        self.db.flush()

    # ------------------------------------------------------------------
    # Métricas de cuenta corriente
    # ------------------------------------------------------------------

    def get_balance_summary_row(self) -> tuple:
        """
        Agrega current_balance de todos los proveedores activos.
        positivo = les debemos | negativo = saldo a nuestro favor.
        """
        stmt = select(
            func.coalesce(
                func.sum(case((Supplier.current_balance > 0, Supplier.current_balance), else_=0)),
                0,
            ),
            func.coalesce(
                func.sum(case((Supplier.current_balance < 0, -Supplier.current_balance), else_=0)),
                0,
            ),
            func.count(case((Supplier.current_balance > 0, 1))),
            func.count(case((Supplier.current_balance < 0, 1))),
        ).where(Supplier.is_active.is_(True))

        return self.db.execute(stmt).one()

    def get_top_by_balance(self, limit: int = 10, ascending: bool = False) -> list[Supplier]:
        """
        Ranking de proveedores por saldo. `ascending=False` trae primero a
        quienes más les debemos; `ascending=True` trae primero a quienes
        tenemos mayor saldo a nuestro favor (balance más negativo).
        """
        order = Supplier.current_balance.asc() if ascending else Supplier.current_balance.desc()
        stmt = (
            select(Supplier)
            .where(Supplier.is_active.is_(True))
            .order_by(order)
            .limit(limit)
        )
        return list(self.db.scalars(stmt).all())