from sqlalchemy import func, select
from sqlalchemy.orm import Session
from app.models.client_model import Client
from app.models.order_model import Order
from app.models.product_model import Product
from app.models.sales_rep_model import SalesRep

class DashboardRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_summary(self) -> dict:
        products_total = self.db.scalar(select(func.count()).select_from(Product)) or 0
        clients_total = self.db.scalar(select(func.count()).select_from(Client)) or 0
        orders_total = self.db.scalar(select(func.count()).select_from(Order)) or 0
        sales_reps_total = self.db.scalar(select(func.count()).select_from(SalesRep)) or 0

        return {
            "products_total": products_total,
            "clients_total": clients_total,
            "orders_total": orders_total,
            "sales_reps_total": sales_reps_total,
        }