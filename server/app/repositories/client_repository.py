from sqlalchemy import case, func, or_, select
from sqlalchemy.orm import Session, joinedload, selectinload
from app.models.client_branch_model import ClientBranch
from app.models.client_model import Client
from app.schemas.client_branch_schema import ClientBranchCreate, ClientBranchUpdate
from app.schemas.client_schema import ClientCreate, ClientUpdate
from app.utils.formatters import normalize_tax_id

class ClientRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, client_id: int) -> Client | None:
        stmt = (
            select(Client)
            .options(
                joinedload(Client.sales_rep),
                selectinload(Client.branches),
            )
            .where(Client.id == client_id)
        )
        return self.db.scalar(stmt)
    
    def get_by_email(self, email: str | None) -> Client | None:
        if not email:
            return None
        stmt = select(Client).where(func.lower(Client.email) == email.strip().lower())
        return self.db.scalar(stmt)

    def get_by_name(
        self,
        name: str,
    ) -> Client | None:

        normalized_name = "".join(
            name.strip().lower().split()
        )

        stmt = select(Client).where(
            func.replace(
                func.lower(Client.name),
                " ",
                "",
            )
            == normalized_name
        )

        return self.db.scalar(stmt)
    
    def get_branch_by_name(
        self,
        client_id: int,
        branch_name: str,
    ) -> ClientBranch | None:

        normalized_name = "".join(
            branch_name.strip().lower().split()
        )

        stmt = select(ClientBranch).where(
            ClientBranch.client_id == client_id,
            func.replace(
                func.lower(ClientBranch.name),
                " ",
                "",
            )
            == normalized_name,
        )

        return self.db.scalar(stmt)

    def get_clients(
        self,
        page: int,
        page_size: int,
        search: str | None = None,
        sales_rep_id: int | None = None,
        is_active: bool | None = None,
        sort: str | None = None,
    ) -> tuple[list[Client], int]:
        stmt = (
            select(Client)
            .options(
                joinedload(Client.sales_rep),
                selectinload(Client.branches),
            )
        )

        if search:
            search_term = f"%{search.strip()}%"
            stmt = stmt.where(Client.name.ilike(search_term))

        if sales_rep_id is not None:
            stmt = stmt.where(Client.sales_rep_id == sales_rep_id)

        if is_active is not None:
            stmt = stmt.where(Client.is_active == is_active)

        normalized_sort = (sort or "").strip().lower()

        if normalized_sort == "name":
            stmt = stmt.order_by(Client.name.asc())
        elif normalized_sort == "created_at":
            stmt = stmt.order_by(Client.created_at.desc())
        else:
            stmt = stmt.order_by(Client.created_at.desc())

        paginated_stmt = stmt.offset((page - 1) * page_size).limit(page_size)
        clients = list(self.db.scalars(paginated_stmt).unique().all())

        count_stmt = select(func.count()).select_from(stmt.order_by(None).subquery())
        total = self.db.scalar(count_stmt) or 0

        return clients, total
    
    def get_by_tax_id(self, tax_id: str) -> Client | None:
        normalized_tax_id = normalize_tax_id(tax_id)
        stmt = select(Client).where(Client.tax_id == normalized_tax_id)
        return self.db.scalar(stmt)

    def create(self, data: ClientCreate, hashed_password: str, refresh: bool = True) -> Client:
        payload = data.model_dump(exclude={"branches", "password"})
        branches_data = data.branches or []

        client = Client(**payload, hashed_password = hashed_password)
        self.db.add(client)
        self.db.flush()

        for branch_data in branches_data:
            branch_payload = (
                branch_data.model_dump()
                if isinstance(branch_data, ClientBranchCreate)
                else branch_data
            )

            branch = ClientBranch(
                client_id=client.id,
                **branch_payload,
            )
            self.db.add(branch)

        self.db.flush()
        if refresh:
            self.db.refresh(client)
        return self.get_by_id(client.id)
    
    def create_no_commit(
        self,
        data: ClientCreate,
        hashed_password: str,
    ) -> Client:

        payload = data.model_dump(
            exclude={"branches", "password"}
        )

        client = Client(**payload, hashed_password=hashed_password)

        self.db.add(client)
        self.db.flush()

        return client

    def update(
        self,
        client: Client,
        data: ClientUpdate,
        hashed_password: str | None = None,
    ) -> Client:
        update_data = data.model_dump(exclude_unset=True, exclude={"branches", "password"})

        for field, value in update_data.items():
            setattr(client, field, value)

        if hashed_password is not None:
            client.hashed_password = hashed_password

        self.db.flush()
        return self.get_by_id(client.id)

    def update_no_commit(
        self,
        client: Client,
        data: ClientUpdate,
        hashed_password: str | None = None,
    ) -> Client:

        update_data = data.model_dump(
            exclude_unset=True,
            exclude={"branches", "password"},
        )

        for field, value in update_data.items():
            setattr(client, field, value)

        if hashed_password is not None:
            client.hashed_password = hashed_password

        self.db.flush()

        return client

    def deactivate(self, client: Client) -> Client:
        client.is_active = False
        self.db.flush()
        return self.get_by_id(client.id)

    def activate(self, client: Client) -> Client:
        client.is_active = True
        self.db.flush()
        return self.get_by_id(client.id)

    def get_branch_by_id(self, branch_id: int) -> ClientBranch | None:
        stmt = select(ClientBranch).where(ClientBranch.id == branch_id)
        return self.db.scalar(stmt)

    def get_branches_by_client_id(self, client_id: int) -> list[ClientBranch]:
        stmt = (
            select(ClientBranch)
            .where(ClientBranch.client_id == client_id)
            .order_by(ClientBranch.is_main.desc(), ClientBranch.created_at.asc())
        )
        return list(self.db.scalars(stmt).all())

    def create_branch(self, client_id: int, data: ClientBranchCreate) -> ClientBranch:
        branch = ClientBranch(
            client_id=client_id,
            **data.model_dump(),
        )
        self.db.add(branch)
        self.db.flush()
        self.db.refresh(branch)
        return branch
    
    def create_branch_no_commit(
        self,
        client_id: int,
        data: ClientBranchCreate,
    ) -> ClientBranch:
        branch = ClientBranch(
            client_id=client_id,
            **data.model_dump(),
        )

        self.db.add(branch)

        self.db.flush()

        return branch

    def update_branch(
        self, branch: ClientBranch, data: ClientBranchUpdate
    ) -> ClientBranch:
        update_data = data.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(branch, field, value)

        self.db.flush()
        self.db.refresh(branch)
        return branch
    
    def update_branch_no_commit(
        self,
        branch: ClientBranch,
        data: ClientBranchUpdate,
    ) -> ClientBranch:
        update_data = data.model_dump(
            exclude_unset=True
        )

        for field, value in update_data.items():
            setattr(branch, field, value)

        self.db.flush()

        return branch

    def deactivate_branch(self, branch: ClientBranch) -> ClientBranch:
        branch.is_active = False
        self.db.flush()
        self.db.refresh(branch)
        return branch

    def activate_branch(self, branch: ClientBranch) -> ClientBranch:
        branch.is_active = True
        self.db.flush()
        self.db.refresh(branch)
        return branch

    def clear_main_branches(
        self,
        client_id: int,
        exclude_branch_id: int | None = None,
    ) -> None:
        stmt = select(ClientBranch).where(
            ClientBranch.client_id == client_id,
            ClientBranch.is_main.is_(True),
        )
        branches = list(self.db.scalars(stmt).all())

        for branch in branches:
            if exclude_branch_id is not None and branch.id == exclude_branch_id:
                continue
            branch.is_main = False

        self.db.flush()

    # ------------------------------------------------------------------
    # Métricas de cuenta corriente
    # ------------------------------------------------------------------

    def get_balance_summary_row(self) -> tuple:
        """
        Agrega current_balance de todos los clientes activos.
        positivo = nos deben (deudores) | negativo = saldo a favor del cliente.
        """
        stmt = select(
            func.coalesce(
                func.sum(case((Client.current_balance > 0, Client.current_balance), else_=0)),
                0,
            ),
            func.coalesce(
                func.sum(case((Client.current_balance < 0, -Client.current_balance), else_=0)),
                0,
            ),
            func.count(case((Client.current_balance > 0, 1))),
            func.count(case((Client.current_balance < 0, 1))),
        ).where(Client.is_active.is_(True))

        return self.db.execute(stmt).one()

    def get_top_by_balance(self, limit: int = 10, ascending: bool = False) -> list[Client]:
        """
        Ranking de clientes por saldo. `ascending=False` trae a los mayores
        deudores primero; `ascending=True` trae a los que tienen mayor saldo
        a favor (balance más negativo) primero.
        """
        order = Client.current_balance.asc() if ascending else Client.current_balance.desc()
        stmt = (
            select(Client)
            .where(Client.is_active.is_(True))
            .order_by(order)
            .limit(limit)
        )
        return list(self.db.scalars(stmt).all())