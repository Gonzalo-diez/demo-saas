from math import ceil
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.core.security import create_access_token, get_password_hash, verify_password
from app.models.client_branch_model import ClientBranch
from app.models.client_model import Client
from app.repositories.client_repository import ClientRepository
from app.schemas.client_branch_schema import (
    ClientBranchCreate,
    ClientBranchResponse,
    ClientBranchUpdate,
)
from app.schemas.client_schema import (
    ClientCreate,
    ClientListResponse,
    ClientLogin,
    ClientMapItem,
    ClientMapResponse,
    ClientResponse,
    ClientUpdate,
)

class ClientService:
    def __init__(self, db: Session):
        self.repository = ClientRepository(db)

    def login(self, data: ClientLogin) -> tuple[Client, str]:
        client = self.repository.get_by_email(data.email)

        if not client or not verify_password(data.password, client.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales inválidas",
            )

        if not client.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="El cliente está inactivo",
            )

        access_token = create_access_token(
            subject=str(client.id),
            token_type="client",
            tenant_id=client.tenant_id,
        )

        return client, access_token

    def get_client_or_404(self, client_id: int) -> Client:
        client = self.repository.get_by_id(client_id)
        if not client:
            raise ValueError("Cliente no encontrado")
        return client

    def get_branch_or_404(self, branch_id: int) -> ClientBranch:
        branch = self.repository.get_branch_by_id(branch_id)
        if not branch:
            raise ValueError("Sucursal no encontrada")
        return branch

    def list_clients(
        self,
        page: int,
        page_size: int,
        search: str | None = None,
        sales_rep_id: int | None = None,
        is_active: bool | None = None,
        sort: str | None = None,
    ) -> ClientListResponse:
        clients, total = self.repository.get_clients(
            page=page,
            page_size=page_size,
            search=search,
            sales_rep_id=sales_rep_id,
            is_active=is_active,
            sort=sort,
        )

        items = [ClientResponse.model_validate(client) for client in clients]
        total_pages = ceil(total / page_size) if total > 0 else 1

        return ClientListResponse(
            clients=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    def get_client(self, client_id: int) -> ClientResponse:
        client = self.get_client_or_404(client_id)
        return ClientResponse.model_validate(client)

    def create_client(self, data: ClientCreate, refresh: bool = True):
        existing_client = self.repository.get_by_email(data.email)

        if existing_client:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ya existe un cliente con ese correo electrónico",
            )
            
        hashed_password = get_password_hash(data.password)
        
        return self.repository.create(
            data=data,
            hashed_password=hashed_password,
            refresh=refresh,
        )

    def update_client(self, client_id: int, data: ClientUpdate) -> ClientResponse:
        client = self.get_client_or_404(client_id)
        hashed_password = (
            get_password_hash(data.password) if data.password else None
        )
        updated_client = self.repository.update(
            client, data, hashed_password=hashed_password
        )
        return ClientResponse.model_validate(updated_client)

    def deactivate_client(self, client_id: int) -> ClientResponse:
        client = self.get_client_or_404(client_id)
        updated_client = self.repository.deactivate(client)
        return ClientResponse.model_validate(updated_client)

    def activate_client(self, client_id: int) -> ClientResponse:
        client = self.get_client_or_404(client_id)
        updated_client = self.repository.activate(client)
        return ClientResponse.model_validate(updated_client)

    def get_clients_for_map(
        self,
        search: str | None = None,
        sales_rep_id: int | None = None,
        is_active: bool | None = None,
    ) -> ClientMapResponse:
        branches = self.repository.get_clients_for_map(
            search=search,
            sales_rep_id=sales_rep_id,
            is_active=is_active,
        )

        items = [
            ClientMapItem(
                client_id=branch.client.id,
                client_name=branch.client.name,
                client_type=branch.client.client_type,
                tax_id=branch.client.tax_id,
                sales_rep_id=branch.client.sales_rep_id,
                sales_rep_name=branch.client.sales_rep.name
                if branch.client.sales_rep
                else None,
                branch_id=branch.id,
                branch_name=branch.name,
                branch_address=branch.address,
                branch_city=branch.city,
                branch_is_main=branch.is_main,
                h3_index=branch.h3_index,
                lat=float(branch.lat),
                lng=float(branch.lng),
                is_active=branch.is_active,
            )
            for branch in branches
        ]

        return ClientMapResponse(clients=items)

    def list_client_branches(self, client_id: int) -> list[ClientBranchResponse]:
        self.get_client_or_404(client_id)
        branches = self.repository.get_branches_by_client_id(client_id)
        return [ClientBranchResponse.model_validate(branch) for branch in branches]

    def create_branch(
        self,
        client_id: int,
        data: ClientBranchCreate,
    ) -> ClientBranchResponse:
        self.get_client_or_404(client_id)

        if data.is_main:
            self.repository.clear_main_branches(client_id)

        branch = self.repository.create_branch(client_id, data)
        return ClientBranchResponse.model_validate(branch)

    def update_branch(
        self,
        client_id: int,
        branch_id: int,
        data: ClientBranchUpdate,
    ) -> ClientBranchResponse:
        self.get_client_or_404(client_id)
        branch = self.get_branch_or_404(branch_id)

        if branch.client_id != client_id:
            raise ValueError("La sucursal no pertenece al cliente indicado")

        if data.is_main is True:
            self.repository.clear_main_branches(
                client_id,
                exclude_branch_id=branch.id,
            )

        updated_branch = self.repository.update_branch(branch, data)
        return ClientBranchResponse.model_validate(updated_branch)

    def deactivate_branch(
        self,
        client_id: int,
        branch_id: int,
    ) -> ClientBranchResponse:
        self.get_client_or_404(client_id)
        branch = self.get_branch_or_404(branch_id)

        if branch.client_id != client_id:
            raise ValueError("La sucursal no pertenece al cliente indicado")

        updated_branch = self.repository.deactivate_branch(branch)
        return ClientBranchResponse.model_validate(updated_branch)

    def activate_branch(
        self,
        client_id: int,
        branch_id: int,
    ) -> ClientBranchResponse:
        self.get_client_or_404(client_id)
        branch = self.get_branch_or_404(branch_id)

        if branch.client_id != client_id:
            raise ValueError("La sucursal no pertenece al cliente indicado")

        updated_branch = self.repository.activate_branch(branch)
        return ClientBranchResponse.model_validate(updated_branch)