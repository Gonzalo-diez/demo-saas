from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload, selectinload
from app.models.client_branch_model import ClientBranch
from app.models.client_model import Client
from app.models.order_model import Order

def _serialize_branch(branch: ClientBranch) -> dict:
    client = branch.client
    sales_rep = client.sales_rep if client else None

    return {
        "branch_id": branch.id,
        "branch_name": branch.name,
        "branch_address": branch.address,
        "branch_city": branch.city,
        "lat": float(branch.lat) if branch.lat is not None else None,
        "lng": float(branch.lng) if branch.lng is not None else None,
        "h3_index": branch.h3_index,
        "is_main": branch.is_main,
        "is_active": branch.is_active,
        "client_id": client.id if client else None,
        "client_name": client.name if client else None,
        "client_type": client.client_type if client else None,
        "sales_rep_id": sales_rep.id if sales_rep else None,
        "sales_rep_name": sales_rep.name if sales_rep else None,
    }

def _serialize_client(client: Client) -> dict:
    return {
        "id": client.id,
        "name": client.name,
        "client_type": client.client_type,
        "address": client.address,
        "city": client.city,
        "lat": float(client.lat) if client.lat is not None else None,
        "lng": float(client.lng) if client.lng is not None else None,
        "h3_index": client.h3_index,
        "sales_rep_id": client.sales_rep_id,
        "sales_rep_name": client.sales_rep.name if client.sales_rep else None,
        "is_active": client.is_active,
        "created_at": client.created_at.isoformat() if client.created_at else None,
        "branches": [
            {
                "id": branch.id,
                "name": branch.name,
                "address": branch.address,
                "city": branch.city,
                "lat": float(branch.lat) if branch.lat is not None else None,
                "lng": float(branch.lng) if branch.lng is not None else None,
                "h3_index": branch.h3_index,
                "is_main": branch.is_main,
                "is_active": branch.is_active,
            }
            for branch in client.branches
        ],
    }

def get_recent_clients_tool(db: Session, limit: int = 10) -> dict:
    stmt = (
        select(Client)
        .options(
            joinedload(Client.sales_rep),
            selectinload(Client.branches),
        )
        .order_by(Client.created_at.desc())
        .limit(limit)
    )

    clients = list(db.scalars(stmt).unique().all())

    return {
        "count": len(clients),
        "items": [_serialize_client(client) for client in clients],
    }

def get_clients_without_sales_rep_tool(db: Session, limit: int = 20) -> dict:
    stmt = (
        select(Client)
        .options(
            joinedload(Client.sales_rep),
            selectinload(Client.branches),
        )
        .where(Client.sales_rep_id.is_(None))
        .order_by(Client.created_at.desc(), Client.name.asc())
        .limit(limit)
    )

    clients = list(db.scalars(stmt).unique().all())

    return {
        "count": len(clients),
        "items": [_serialize_client(client) for client in clients],
    }

def get_clients_by_sales_rep_tool(db: Session, sales_rep_id: int, limit: int = 20) -> dict:
    stmt = (
        select(Client)
        .options(
            joinedload(Client.sales_rep),
            selectinload(Client.branches),
        )
        .where(Client.sales_rep_id == sales_rep_id)
        .order_by(Client.name.asc())
        .limit(limit)
    )

    clients = list(db.scalars(stmt).unique().all())

    return {
        "sales_rep_id": sales_rep_id,
        "count": len(clients),
        "items": [_serialize_client(client) for client in clients],
    }

def get_clients_with_coordinates_tool(db: Session, limit: int = 20) -> dict:
    stmt = (
        select(ClientBranch)
        .options(
            joinedload(ClientBranch.client).joinedload(Client.sales_rep),
        )
        .where(
            ClientBranch.lat.is_not(None),
            ClientBranch.lng.is_not(None),
            ClientBranch.is_active.is_(True),
        )
        .order_by(ClientBranch.client_id.asc(), ClientBranch.is_main.desc(), ClientBranch.name.asc())
        .limit(limit)
    )

    branches = list(db.scalars(stmt).unique().all())

    return {
        "count": len(branches),
        "items": [_serialize_branch(branch) for branch in branches],
    }

def get_clients_without_orders_tool(db: Session, limit: int = 20) -> dict:
    subquery = select(Order.client_id).distinct()

    stmt = (
        select(Client)
        .options(
            joinedload(Client.sales_rep),
            selectinload(Client.branches),
        )
        .where(Client.id.not_in(subquery))
        .order_by(Client.created_at.desc(), Client.name.asc())
        .limit(limit)
    )

    clients = list(db.scalars(stmt).unique().all())

    return {
        "count": len(clients),
        "items": [_serialize_client(client) for client in clients],
    }

def get_branches_without_orders_tool(db: Session, limit: int = 20) -> dict:
    subquery = select(Order.client_branch_id).where(Order.client_branch_id.is_not(None)).distinct()

    stmt = (
        select(ClientBranch)
        .options(
            joinedload(ClientBranch.client).joinedload(Client.sales_rep),
        )
        .where(ClientBranch.id.not_in(subquery))
        .where(ClientBranch.is_active.is_(True))
        .order_by(ClientBranch.client_id.asc(), ClientBranch.is_main.desc(), ClientBranch.name.asc())
        .limit(limit)
    )

    branches = list(db.scalars(stmt).unique().all())

    return {
        "count": len(branches),
        "items": [_serialize_branch(branch) for branch in branches],
    }

def get_client_overview_tool(db: Session) -> dict:
    total_clients = db.scalar(select(func.count()).select_from(Client)) or 0
    active_clients = db.scalar(
        select(func.count()).select_from(Client).where(Client.is_active.is_(True))
    ) or 0
    inactive_clients = db.scalar(
        select(func.count()).select_from(Client).where(Client.is_active.is_(False))
    ) or 0
    clients_without_sales_rep = db.scalar(
        select(func.count()).select_from(Client).where(Client.sales_rep_id.is_(None))
    ) or 0

    total_branches = db.scalar(select(func.count()).select_from(ClientBranch)) or 0
    active_branches = db.scalar(
        select(func.count()).select_from(ClientBranch).where(ClientBranch.is_active.is_(True))
    ) or 0
    branches_with_coordinates = db.scalar(
        select(func.count())
        .select_from(ClientBranch)
        .where(ClientBranch.lat.is_not(None), ClientBranch.lng.is_not(None))
    ) or 0
    main_branches = db.scalar(
        select(func.count()).select_from(ClientBranch).where(ClientBranch.is_main.is_(True))
    ) or 0

    cities_stmt = (
        select(ClientBranch.city, func.count(ClientBranch.id))
        .where(ClientBranch.city.is_not(None))
        .group_by(ClientBranch.city)
        .order_by(func.count(ClientBranch.id).desc(), ClientBranch.city.asc())
        .limit(10)
    )
    top_cities = [
        {"city": city, "count": count}
        for city, count in db.execute(cities_stmt).all()
    ]

    return {
        "totals": {
            "clients_total": total_clients,
            "active_clients": active_clients,
            "inactive_clients": inactive_clients,
            "clients_without_sales_rep": clients_without_sales_rep,
            "branches_total": total_branches,
            "active_branches": active_branches,
            "branches_with_coordinates": branches_with_coordinates,
            "main_branches": main_branches,
        },
        "top_branch_cities": top_cities,
    }