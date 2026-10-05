"""categorías por tenant + publicación (is_public) de categorías y productos

Revision ID: 7c1d9e4a52b8
Revises: 53d678be9feb
Create Date: 2026-10-02 03:00:00

Antes las categorías eran una lista fija en el código y "público" se deducía de
si la categoría estaba en esa lista. Ahora:

- categories: tabla por tenant (name, slug, is_public, requires_age_verification).
- products.category_id: FK a la categoría.
- products.is_public: publicación explícita por producto.

Data migration: por cada (tenant, categoría distinta) ya usada por productos se
crea una fila en categories y se enlaza. Las que eran de la lista fija del
catálogo quedan públicas (y las de tabaco con verificación de edad); las
"libres" quedan privadas, igual que se comportaban antes.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "7c1d9e4a52b8"
down_revision: Union[str, None] = "53d678be9feb"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Lista fija que existía en el código (category_normalizer.py), solo para migrar datos.
_LEGACY_CATALOG = ("analgesicos", "cigarrillos eco", "masalin bat", "tabaco accesorios", "pegamentos", "pilas", "preservativos")
_LEGACY_REGULATED = ("cigarrillos eco", "masalin bat", "tabaco accesorios")
_LEGACY_LABELS = {
    "analgesicos": "Analgésicos",
    "cigarrillos eco": "Cigarrillos Eco",
    "masalin bat": "Masalin Bat",
    "tabaco accesorios": "Tabaco & Accesorios",
    "pegamentos": "Pegamentos",
    "pilas": "Pilas",
    "preservativos": "Preservativos",
}


def upgrade() -> None:
    op.create_table(
        "categories",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("name_normalized", sa.String(length=100), nullable=False),
        sa.Column("slug", sa.String(length=120), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=True),
        sa.Column("is_public", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("requires_age_verification", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "name_normalized", name="uq_categories_tenant_name"),
        sa.UniqueConstraint("tenant_id", "slug", name="uq_categories_tenant_slug"),
    )
    op.create_index(op.f("ix_categories_id"), "categories", ["id"], unique=False)
    op.create_index(op.f("ix_categories_tenant_id"), "categories", ["tenant_id"], unique=False)
    op.create_index(op.f("ix_categories_name_normalized"), "categories", ["name_normalized"], unique=False)

    op.add_column("products", sa.Column("category_id", sa.Integer(), nullable=True))
    op.add_column("products", sa.Column("is_public", sa.Boolean(), server_default="true", nullable=False))
    op.create_index(op.f("ix_products_category_id"), "products", ["category_id"], unique=False)
    op.create_foreign_key(
        "products_category_id_fkey", "products", "categories", ["category_id"], ["id"], ondelete="SET NULL"
    )

    _migrate_existing_data()


def _migrate_existing_data() -> None:
    bind = op.get_bind()
    rows = bind.execute(
        sa.text(
            "SELECT tenant_id, category_normalized, MIN(category) AS category "
            "FROM products "
            "WHERE category IS NOT NULL AND category_normalized <> 'sin clasificar' "
            "GROUP BY tenant_id, category_normalized"
        )
    ).all()

    used_slugs: set[tuple[int, str]] = set()
    for tenant_id, normalized, raw_name in rows:
        legacy = normalized in _LEGACY_CATALOG
        name = _LEGACY_LABELS.get(normalized, raw_name)
        base_slug = _slugify(name) or "categoria"
        slug, n = base_slug, 2
        while (tenant_id, slug) in used_slugs:
            slug, n = f"{base_slug}-{n}", n + 1
        used_slugs.add((tenant_id, slug))

        category_id = bind.execute(
            sa.text(
                "INSERT INTO categories (tenant_id, name, name_normalized, slug, is_public, requires_age_verification) "
                "VALUES (:t, :n, :nn, :s, :pub, :age) RETURNING id"
            ),
            {
                "t": tenant_id, "n": name, "nn": _normalize(name), "s": slug,
                "pub": legacy, "age": normalized in _LEGACY_REGULATED,
            },
        ).scalar_one()

        bind.execute(
            sa.text(
                "UPDATE products SET category_id = :cid, category = :n, category_normalized = :nn "
                "WHERE tenant_id = :t AND category_normalized = :old"
            ),
            {"cid": category_id, "n": name, "nn": _normalize(name), "t": tenant_id, "old": normalized},
        )


def _normalize(value: str) -> str:
    import re
    import unicodedata

    value = unicodedata.normalize("NFKD", value.strip().lower())
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", value)


def _slugify(value: str) -> str:
    import re
    import unicodedata

    value = unicodedata.normalize("NFD", value)
    value = "".join(ch for ch in value if unicodedata.category(ch) != "Mn").lower().strip()
    value = re.sub(r"[^a-z0-9\s-]", "", value)
    value = re.sub(r"[\s_-]+", "-", value)
    return re.sub(r"^-+|-+$", "", value)


def downgrade() -> None:
    op.drop_constraint("products_category_id_fkey", "products", type_="foreignkey")
    op.drop_index(op.f("ix_products_category_id"), table_name="products")
    op.drop_column("products", "is_public")
    op.drop_column("products", "category_id")
    op.drop_index(op.f("ix_categories_name_normalized"), table_name="categories")
    op.drop_index(op.f("ix_categories_tenant_id"), table_name="categories")
    op.drop_index(op.f("ix_categories_id"), table_name="categories")
    op.drop_table("categories")
