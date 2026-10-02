from io import BytesIO
import secrets
import pandas as pd
from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy.orm import Session
from app.core.security import get_password_hash
from app.repositories.client_repository import ClientRepository
from app.schemas.client_branch_schema import (
    ClientBranchCreate,
    ClientBranchUpdate,
)
from app.schemas.client_schema import (
    ClientCreate,
    ClientUpdate,
)
from app.schemas.client_import_schema import (
    ClientImportCommitResponse,
    ClientImportPreviewItem,
    ClientImportPreviewResponse,
    ClientImportRow,
    ClientImportRowError,
    GeneratedClientPassword,
)

class ClientImportService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = ClientRepository(db)

    def parse_file(
        self,
        content: bytes,
        filename: str,
    ) -> tuple[list[ClientImportRow], list[ClientImportRowError]]:
        filename_lower = filename.lower()

        try:
            if filename_lower.endswith(".csv"):
                df = pd.read_csv(BytesIO(content))

            elif filename_lower.endswith((".xlsx", ".xls")):
                df = pd.read_excel(BytesIO(content))

            else:
                raise ValueError(
                    "Formato no soportado. Use CSV o Excel."
                )

        except ValueError:
            raise

        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Error al leer el archivo: {e}",
            )

        df = df.where(pd.notnull(df), None)

        df.columns = [
            str(col).strip().lower()
            for col in df.columns
        ]

        valid: list[ClientImportRow] = []
        invalid: list[ClientImportRowError] = []

        for index, row in enumerate(df.itertuples(index=False), start=2):
            row_dict = row._asdict()

            try:
                valid.append(
                    ClientImportRow(
                        client_name=row_dict.get("client_name"),
                        tax_id=row_dict.get("tax_id"),
                        client_type=row_dict.get("client_type", "company"),
                        is_active=row_dict.get("is_active", True),
                        branch_name=row_dict.get("branch_name"),
                        address=row_dict.get("address"),
                        city=row_dict.get("city"),
                        lat=row_dict.get("lat"),
                        lng=row_dict.get("lng"),
                        contact_name=row_dict.get("contact_name"),
                        contact_phone=row_dict.get("contact_phone"),
                        reference=row_dict.get("reference"),
                        is_main=row_dict.get("is_main", False),
                        branch_is_active=row_dict.get("branch_is_active", True),
                    )
                )

            except ValidationError as exc:
                errors = [
                    f"{'.'.join(str(loc) for loc in err['loc'])}: {err['msg']}"
                    for err in exc.errors()
                ]
                invalid.append(
                    ClientImportRowError(
                        row_number=index,
                        data=row_dict,
                        errors=errors,
                    )
                )

        return valid, invalid

    def _find_client(
        self,
        row: ClientImportRow,
    ):
        if row.tax_id:
            client = self.repo.get_by_tax_id(row.tax_id)

            if client:
                return client

        return self.repo.get_by_name(row.client_name)

    def _find_branch(
        self,
        client_id: int,
        row: ClientImportRow,
    ):
        return self.repo.get_branch_by_name(
            client_id,
            row.branch_name,
        )

    def preview_import(
        self,
        content: bytes,
        filename: str,
    ) -> ClientImportPreviewResponse:
        rows_valid, rows_invalid = self.parse_file(content, filename)

        items: list[ClientImportPreviewItem] = []

        clients_to_create = 0
        clients_to_update = 0
        branches_to_create = 0
        branches_to_update = 0
        skipped_rows = 0

        # items de error por filas inválidas
        for entry in rows_invalid:
            items.append(
                ClientImportPreviewItem(
                    row_number=entry.row_number,
                    client_name=str(entry.data.get("client_name") or ""),
                    branch_name=str(entry.data.get("branch_name") or ""),
                    client_action="error",
                    branch_action="error",
                    errors=entry.errors,
                )
            )

        # items de filas válidas con acción determinada
        confirmed_valid: list[ClientImportRow] = []

        for index, row in enumerate(rows_valid, start=1):
            try:
                client = self._find_client(row)

                if client:
                    client_action = "update"
                    clients_to_update += 1
                    branch = self._find_branch(client.id, row)

                    if branch:
                        branch_action = "update"
                        branches_to_update += 1
                    else:
                        branch_action = "create"
                        branches_to_create += 1

                else:
                    client_action = "create"
                    branch_action = "create"
                    clients_to_create += 1
                    branches_to_create += 1

                confirmed_valid.append(row)
                items.append(
                    ClientImportPreviewItem(
                        row_number=index,
                        client_name=row.client_name,
                        branch_name=row.branch_name,
                        client_action=client_action,
                        branch_action=branch_action,
                        errors=[],
                    )
                )

            except Exception as e:
                skipped_rows += 1
                items.append(
                    ClientImportPreviewItem(
                        row_number=index,
                        client_name=row.client_name,
                        branch_name=row.branch_name,
                        client_action="error",
                        branch_action="error",
                        errors=[str(e)],
                    )
                )

        return ClientImportPreviewResponse(
            total_rows=len(rows_valid) + len(rows_invalid),
            clients_to_create=clients_to_create,
            clients_to_update=clients_to_update,
            branches_to_create=branches_to_create,
            branches_to_update=branches_to_update,
            valid_rows=len(confirmed_valid),
            invalid_rows=len(rows_invalid),
            skipped_rows=skipped_rows,
            items=items,
            rows_valid=confirmed_valid,
            rows_invalid=rows_invalid,
        )

    def import_clients_bulk(
        self,
        rows: list[ClientImportRow],
        mode: str = "upsert",
    ) -> dict:
        clients_created = 0
        clients_updated = 0
        branches_created = 0
        branches_updated = 0
        skipped_rows = 0
        generated_passwords: list[GeneratedClientPassword] = []

        for row in rows:
            try:
                client = self._find_client(row)

                # --- lógica de mode para el cliente ---
                if not client:
                    if mode == "update":
                        # solo actualizar existentes: saltear
                        skipped_rows += 1
                        continue

                    # Si no vino contraseña en la fila, se genera una
                    # aleatoria para que el cliente pueda loguearse; se
                    # informa en la respuesta para que se le pueda avisar.
                    plain_password = row.password or secrets.token_urlsafe(8)

                    client = self.repo.create_no_commit(
                        ClientCreate(
                            name=row.client_name,
                            tax_id=row.tax_id,
                            email=row.email,
                            client_type=row.client_type,
                            is_active=row.is_active,
                            password=plain_password,
                        ),
                        hashed_password=get_password_hash(plain_password),
                    )
                    clients_created += 1

                    if not row.password:
                        generated_passwords.append(
                            GeneratedClientPassword(
                                client_name=row.client_name,
                                email=row.email,
                                password=plain_password,
                            )
                        )

                else:
                    if mode == "create":
                        # solo crear nuevos: saltear existentes
                        skipped_rows += 1
                        continue

                    # La contraseña solo se toca si vino explícitamente en
                    # la fila; si no, se conserva la que ya tenía el
                    # cliente (re-importar para actualizar dirección/CUIT
                    # no debería resetear el login de nadie).
                    hashed_password = (
                        get_password_hash(row.password)
                        if row.password
                        else None
                    )

                    self.repo.update_no_commit(
                        client,
                        ClientUpdate(
                            name=row.client_name,
                            tax_id=row.tax_id,
                            email=row.email,
                            client_type=row.client_type,
                            is_active=row.is_active,
                        ),
                        hashed_password=hashed_password,
                    )
                    clients_updated += 1

                # --- lógica de mode para la sucursal ---
                branch = self._find_branch(client.id, row)

                if not branch:
                    if mode == "update":
                        skipped_rows += 1
                        continue

                    if row.is_main:
                        self.repo.clear_main_branches(client.id)

                    self.repo.create_branch_no_commit(
                        client.id,
                        ClientBranchCreate(
                            name=row.branch_name,
                            address=row.address,
                            city=row.city,
                            lat=row.lat,
                            lng=row.lng,
                            contact_name=row.contact_name,
                            contact_phone=row.contact_phone,
                            reference=row.reference,
                            is_main=row.is_main,
                            is_active=row.branch_is_active,
                        ),
                    )
                    branches_created += 1

                else:
                    if mode == "create":
                        skipped_rows += 1
                        continue

                    if row.is_main:
                        self.repo.clear_main_branches(
                            client.id,
                            exclude_branch_id=branch.id,
                        )

                    self.repo.update_branch_no_commit(
                        branch,
                        ClientBranchUpdate(
                            name=row.branch_name,
                            address=row.address,
                            city=row.city,
                            lat=row.lat,
                            lng=row.lng,
                            contact_name=row.contact_name,
                            contact_phone=row.contact_phone,
                            reference=row.reference,
                            is_main=row.is_main,
                            is_active=row.branch_is_active,
                        ),
                    )
                    branches_updated += 1

            except Exception:
                skipped_rows += 1

        return {
            "clients_created": clients_created,
            "clients_updated": clients_updated,
            "branches_created": branches_created,
            "branches_updated": branches_updated,
            "skipped_rows": skipped_rows,
            "generated_passwords": generated_passwords,
        }

    def commit_from_rows(
        self,
        rows: list[ClientImportRow],
        mode: str,
    ) -> ClientImportCommitResponse:
        result = self.import_clients_bulk(
            rows,
            mode=mode,
        )

        return ClientImportCommitResponse(**result)

    def commit_import(
        self,
        content: bytes,
        filename: str,
        mode: str = "upsert",
    ) -> ClientImportCommitResponse:
        rows_valid, _ = self.parse_file(content, filename)

        result = self.import_clients_bulk(
            rows_valid,
            mode=mode,
        )

        return ClientImportCommitResponse(**result)