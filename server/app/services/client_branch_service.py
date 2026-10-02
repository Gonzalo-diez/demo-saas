from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.repositories.client_repository import ClientRepository
from app.schemas.client_branch_schema import (
    ClientBranchCreate,
    ClientBranchUpdate,
)
from app.utils.geo import compute_h3

class ClientBranchService:
    def __init__(self, db: Session):
        self.repo = ClientRepository(db)

    def _get_client(self, client_id: int):
        client = self.repo.get_by_id(client_id)

        if not client:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cliente no encontrado",
            )

        return client

    def _get_branch(self, branch_id: int):
        branch = self.repo.get_branch_by_id(branch_id)

        if not branch:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Sucursal no encontrada",
            )

        return branch

    def _validate_geo(self, lat, lng) -> None:
        try:
            compute_h3(lat, lng)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            )

    def list_by_client(self, client_id: int):
        self._get_client(client_id)

        branches = self.repo.get_branches_by_client_id(client_id)

        return {"branches": branches}

    def create(self, client_id: int, data: ClientBranchCreate):
        self._get_client(client_id)

        self._validate_geo(data.lat, data.lng)

        if data.is_main:
            self.repo.clear_main_branches(client_id)

        branch = self.repo.create_branch(client_id, data)

        # si es la primera sucursal del cliente, forzar principal
        branches = self.repo.get_branches_by_client_id(client_id)

        if len(branches) == 1 and not branch.is_main:
            branch = self.repo.update_branch(
                branch,
                ClientBranchUpdate(is_main=True),
            )

        return branch

    def update(self, branch_id: int, data: ClientBranchUpdate):
        branch = self._get_branch(branch_id)

        if data.lat is not None or data.lng is not None:
            lat = (
                data.lat
                if "lat" in data.model_fields_set
                else branch.lat
            )

            lng = (
                data.lng
                if "lng" in data.model_fields_set
                else branch.lng
            )

            self._validate_geo(lat, lng)

        if data.is_main is True:
            self.repo.clear_main_branches(
                branch.client_id,
                exclude_branch_id=branch.id,
            )

        updated = self.repo.update_branch(branch, data)

        return updated

    def deactivate(self, branch_id: int):
        branch = self._get_branch(branch_id)

        if branch.is_main:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se puede desactivar la sucursal principal",
            )

        return self.repo.deactivate_branch(branch)

    def activate(self, branch_id: int):
        branch = self._get_branch(branch_id)

        return self.repo.activate_branch(branch)