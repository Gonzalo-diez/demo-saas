from io import BytesIO

import pandas as pd
from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.repositories.supplier_repository import (
    SupplierRepository,
)
from app.schemas.supplier_schema import (
    SupplierCreate,
    SupplierUpdate,
)
from app.schemas.supplier_import_schema import (
    SupplierImportCommitRequest,
    SupplierImportCommitResponse,
    SupplierImportPreviewItem,
    SupplierImportPreviewResponse,
    SupplierImportRow,
    SupplierImportRowError,
)


class SupplierImportService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = SupplierRepository(db)

    # =====================================================
    # FILE PARSER
    # =====================================================

    def parse_file(
        self,
        content: bytes,
        filename: str,
    ) -> tuple[
        list[SupplierImportRow],
        list[SupplierImportRowError],
    ]:
        filename_lower = filename.lower()

        try:
            if filename_lower.endswith(".csv"):
                df = pd.read_csv(
                    BytesIO(content)
                )

            elif filename_lower.endswith(
                (".xlsx", ".xls")
            ):
                df = pd.read_excel(
                    BytesIO(content)
                )

            else:
                raise ValueError(
                    "Formato no soportado. Use CSV o Excel."
                )

        except ValueError:
            raise

        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Error al leer el archivo: {e}"
                ),
            )

        df = df.where(
            pd.notnull(df),
            None,
        )

        df.columns = [
            str(col).strip().lower()
            for col in df.columns
        ]

        rows_valid: list[
            SupplierImportRow
        ] = []

        rows_invalid: list[
            SupplierImportRowError
        ] = []

        for index, row in enumerate(
            df.itertuples(index=False),
            start=2,
        ):
            row_dict = row._asdict()

            try:
                rows_valid.append(
                    SupplierImportRow(
                        name=row_dict.get("name"),
                        tax_id=row_dict.get(
                            "tax_id"
                        ),
                        email=row_dict.get(
                            "email"
                        ),
                        phone=row_dict.get(
                            "phone"
                        ),
                        address=row_dict.get(
                            "address"
                        ),
                    )
                )

            except ValidationError as exc:
                errors = [
                    (
                        f"{'.'.join(str(loc) for loc in err['loc'])}: "
                        f"{err['msg']}"
                    )
                    for err in exc.errors()
                ]

                rows_invalid.append(
                    SupplierImportRowError(
                        row_number=index,
                        data=row_dict,
                        errors=errors,
                    )
                )

        return (
            rows_valid,
            rows_invalid,
        )

    # =====================================================
    # HELPERS
    # =====================================================

    def _find_existing_supplier(
        self,
        row: SupplierImportRow,
    ):
        if row.tax_id:
            supplier = (
                self.repo.get_by_tax_id(
                    row.tax_id
                )
            )

            if supplier:
                return supplier

        return self.repo.get_by_name(
            row.name
        )

    # =====================================================
    # PREVIEW
    # =====================================================

    def preview_import(
        self,
        content: bytes,
        filename: str,
    ) -> SupplierImportPreviewResponse:

        rows_valid, rows_invalid = (
            self.parse_file(
                content,
                filename,
            )
        )

        items: list[
            SupplierImportPreviewItem
        ] = []

        create_count = 0
        update_count = 0
        skip_count = len(rows_invalid)

        for row_error in rows_invalid:
            items.append(
                SupplierImportPreviewItem(
                    row_number=row_error.row_number,
                    name=str(
                        row_error.data.get(
                            "name"
                        )
                        or ""
                    ),
                    action="error",
                    errors=row_error.errors,
                )
            )

        for index, row in enumerate(
            rows_valid,
            start=2,
        ):
            try:
                existing = (
                    self._find_existing_supplier(
                        row
                    )
                )

                if existing:
                    action = "update"
                    update_count += 1

                else:
                    action = "create"
                    create_count += 1

                items.append(
                    SupplierImportPreviewItem(
                        row_number=index,
                        name=row.name,
                        action=action,
                        errors=[],
                    )
                )

            except Exception as e:
                skip_count += 1

                items.append(
                    SupplierImportPreviewItem(
                        row_number=index,
                        name=row.name,
                        action="error",
                        errors=[str(e)],
                    )
                )

        return (
            SupplierImportPreviewResponse(
                total_rows=(
                    len(rows_valid)
                    + len(rows_invalid)
                ),
                valid_rows=len(
                    rows_valid
                ),
                invalid_rows=len(
                    rows_invalid
                ),
                rows_valid=rows_valid,
                rows_invalid=rows_invalid,
                create_count=create_count,
                update_count=update_count,
                skip_count=skip_count,
                items=items,
            )
        )

    # =====================================================
    # BULK IMPORT
    # =====================================================

    def import_suppliers_bulk(
        self,
        rows: list[
            SupplierImportRow
        ],
        mode: str = "upsert",
    ) -> dict:

        created_count = 0
        updated_count = 0
        skipped_count = 0

        for row in rows:

            try:
                existing = (
                    self._find_existing_supplier(
                        row
                    )
                )

                if existing:

                    if (
                        mode
                        == "skip_existing"
                    ):
                        skipped_count += 1
                        continue

                    update_schema = (
                        SupplierUpdate(
                            **row.model_dump(
                                exclude_unset=True
                            )
                        )
                    )

                    self.repo.update_no_commit(
                        existing,
                        update_schema,
                    )

                    updated_count += 1

                else:

                    create_schema = (
                        SupplierCreate(
                            **row.model_dump()
                        )
                    )

                    self.repo.create_no_commit(
                        create_schema
                    )

                    created_count += 1

            except Exception:
                skipped_count += 1

        return {
            "created": created_count,
            "updated": updated_count,
            "skipped": skipped_count,
        }

    # =====================================================
    # COMMIT
    # =====================================================

    def commit_import(
        self,
        request: SupplierImportCommitRequest,
    ) -> SupplierImportCommitResponse:

        result = (
            self.import_suppliers_bulk(
                rows=request.rows,
                mode=request.mode,
            )
        )

        return (
            SupplierImportCommitResponse(
                created=result["created"],
                updated=result["updated"],
                skipped=result["skipped"],
            )
        )