import io
import math
import pandas as pd
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.repositories.sales_rep_repository import SalesRepRepository
from app.schemas.sales_rep_import_schema import (
    SalesRepImportCommitRequest,
    SalesRepImportCommitResponse,
    SalesRepImportPreviewResponse,
    SalesRepImportRow,
    SalesRepImportRowError,
)
from app.schemas.sales_rep_schema import (
    SalesRepCreate,
    SalesRepUpdate,
)
from app.services.sales_rep_service import SalesRepService

class SalesRepImportService:
    def __init__(self, db: Session):
        self.db = db
        self.sales_rep_repo = SalesRepRepository(db)
        self.sales_rep_service = SalesRepService(db)

    def preview(
        self,
        file_bytes: bytes,
    ) -> SalesRepImportPreviewResponse:
        try:
            df = pd.read_excel(io.BytesIO(file_bytes))

            # reemplazar NaN por None
            df = df.where(pd.notnull(df), None)

        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Error al leer Excel: {str(e)}",
            )

        required_columns = {
            "name",
            "email",
            "password",
        }

        missing_columns = required_columns - set(df.columns)

        if missing_columns:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Faltan columnas requeridas: "
                    f"{', '.join(sorted(missing_columns))}"
                ),
            )

        rows_valid: list[SalesRepImportRow] = []
        rows_invalid: list[SalesRepImportRowError] = []

        seen_emails: set[str] = set()

        for index, row in df.iterrows():
            row_dict = {
                k: (None if pd.isna(v) else v)
                for k, v in row.to_dict().items()
            }

            # +2 -> header + index 0
            row_number = index + 2

            try:
                valid_row = SalesRepImportRow(**row_dict)

                normalized_email = (
                    valid_row.email.strip().lower()
                )

                if normalized_email in seen_emails:

                    rows_invalid.append(
                        SalesRepImportRowError(
                            row_number=row_number,
                            data=row_dict,
                            errors=[
                                (
                                    "email duplicado "
                                    "dentro del archivo"
                                )
                            ],
                        )
                    )

                    continue

                seen_emails.add(normalized_email)

                rows_valid.append(valid_row)

            except Exception as e:
                errors = []

                if hasattr(e, "errors"):
                    for err in e.errors():
                        loc = err.get("loc", ())

                        if len(loc) > 0:
                            errors.append(
                                f"{loc[0]}: {err['msg']}"
                            )
                        else:
                            errors.append(
                                err["msg"]
                            )
                else:
                    errors.append(str(e))

                rows_invalid.append(
                    SalesRepImportRowError(
                        row_number=row_number,
                        data=row_dict,
                        errors=errors,
                    )
                )

        return SalesRepImportPreviewResponse(
            total_rows=len(df),
            valid_rows=len(rows_valid),
            invalid_rows=len(rows_invalid),
            rows_valid=rows_valid,
            rows_invalid=rows_invalid,
        )

    def commit(
        self,
        data: SalesRepImportCommitRequest,
    ) -> SalesRepImportCommitResponse:

        created_count = 0
        updated_count = 0

        errors: list[str] = []

        total_to_process = len(data.rows)

        try:

            for row in data.rows:

                normalized_email = (
                    row.email.strip().lower()
                )

                existing_sales_rep = (
                    self.sales_rep_repo.get_by_email(
                        normalized_email
                    )
                )

                # CREATE MODE
                if data.mode == "create":

                    if existing_sales_rep:
                        errors.append(
                            (
                                f"El vendedor con email "
                                f"{normalized_email} ya existe"
                            )
                        )
                        continue

                    sales_rep_create = SalesRepCreate(
                        name=row.name,
                        email=normalized_email,
                        phone=row.phone,
                        password=row.password,
                        is_active=row.is_active,
                        is_superuser=row.is_superuser,
                        home_lat=row.home_lat,
                        home_lng=row.home_lng,
                        coverage_radius_km=row.coverage_radius_km,
                    )

                    self.sales_rep_service.create(
                        sales_rep_create,
                        refresh=False,
                    )

                    created_count += 1

                # UPSERT MODE
                elif data.mode == "upsert":

                    if existing_sales_rep:

                        update_data = SalesRepUpdate(
                            name=row.name,
                            phone=row.phone,
                            is_active=row.is_active,
                            is_superuser=row.is_superuser,
                            home_lat=row.home_lat,
                            home_lng=row.home_lng,
                            coverage_radius_km=row.coverage_radius_km,
                        )

                        self.sales_rep_service.update(
                            sales_rep=existing_sales_rep,
                            data=update_data,
                            refresh=False,
                        )

                        # actualizar password opcionalmente
                        if row.password:

                            self.sales_rep_service.update_password(
                                sales_rep=existing_sales_rep,
                                new_password=row.password,
                                refresh=False,
                            )

                        updated_count += 1

                    else:

                        sales_rep_create = SalesRepCreate(
                            name=row.name,
                            email=normalized_email,
                            phone=row.phone,
                            password=row.password,
                            is_active=row.is_active,
                            is_superuser=row.is_superuser,
                            home_lat=row.home_lat,
                            home_lng=row.home_lng,
                            coverage_radius_km=row.coverage_radius_km,
                        )

                        self.sales_rep_service.create(
                            sales_rep_create,
                            refresh=False,
                        )

                        created_count += 1

        except Exception as e:

            self.db.rollback()

            raise HTTPException(
                status_code=500,
                detail=f"Error durante importación: {str(e)}",
            )

        return SalesRepImportCommitResponse(
            total=total_to_process,
            created=created_count,
            updated=updated_count,
            failed=len(errors),
            errors=errors,
        )