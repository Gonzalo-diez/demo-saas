from typing import List, Optional, Tuple
from datetime import date, datetime, UTC
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload
from app.models.order_model import Order
from app.models.order_item_model import OrderItem
from app.schemas.order_schema import (
    OrderCreateShop,
    OrderCreateB2B,
    OrderUpdateShop,
    OrderUpdateB2B,
    OrderUpdateStatus,
    OrderEditShop,
    OrderEditB2B,
)

class OrderRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_order_shop(self, *, obj_in: OrderCreateShop, total_data: dict) -> Order:
        db_obj = Order(
            sales_type="ONLINE",
            customer_name=obj_in.customer_name,
            customer_phone=obj_in.customer_phone,
            customer_email=obj_in.customer_email,
            customer_dni=obj_in.customer_dni,
            age_confirmed=obj_in.age_confirmed,
            customer_tax_id=obj_in.customer_tax_id,
            customer_person_type=obj_in.customer_person_type,
            customer_iva_condition=obj_in.customer_iva_condition,
            client_id=total_data.get("client_id"),
            client_snapshot=total_data.get("client_snapshot"),
            client_branch_id=obj_in.client_branch_id,
            client_branch_snapshot=total_data.get("client_branch_snapshot"),
            delivery_type=obj_in.delivery_type,
            delivery_address=obj_in.delivery_address,
            delivery_city=obj_in.delivery_city,
            delivery_reference=obj_in.delivery_reference,
            preferred_delivery_date=obj_in.preferred_delivery_date,
            currency=obj_in.currency,
            document_type=obj_in.document_type,
            status="pending_confirmation",
            total_amount=total_data["total_amount"],
            total_cost=total_data["total_cost"],
            margin_amount=total_data["margin_amount"],
        )

        self.db.add(db_obj)
        self.db.flush()

        items = [
            OrderItem(
                order_id=db_obj.id,
                product_id=item["product_id"],
                product_name_snapshot=item["product_name"],
                product_brand_snapshot=item.get("product_brand"),
                product_sku_snapshot=item.get("product_sku"),
                product_image_url_snapshot=item.get("product_image_url"),
                quantity=item["quantity"],
                unit_price=item["unit_price"],
                unit_cost=item["unit_cost"],
                subtotal=item["subtotal"],
                subtotal_cost=item["subtotal_cost"],
                margin_amount=item["margin_amount"],
            )
            for item in total_data["items"]
        ]

        self.db.add_all(items)

        self.db.flush()
        self.db.refresh(db_obj)

        return db_obj

    def create_order_b2b(
        self,
        *,
        obj_in: OrderCreateB2B,
        sales_rep_id: int,
        total_data: dict,
    ) -> Order:
        db_obj = Order(
            sales_type="B2B",
            client_id=obj_in.client_id,
            client_branch_id=obj_in.client_branch_id,
            client_snapshot=total_data["client_snapshot"],
            client_branch_snapshot=total_data["client_branch_snapshot"],
            sales_rep_snapshot=total_data["sales_rep_snapshot"],
            sales_rep_id=sales_rep_id,
            currency=obj_in.currency,
            document_type=obj_in.document_type,
            status="pending_confirmation",
            total_amount=total_data["total_amount"],
            total_cost=total_data["total_cost"],
            margin_amount=total_data["margin_amount"],
        )

        self.db.add(db_obj)
        self.db.flush()

        items = [
            OrderItem(
                order_id=db_obj.id,
                product_id=item["product_id"],
                product_name_snapshot=item["product_name"],
                product_brand_snapshot=item.get("product_brand"),
                product_sku_snapshot=item.get("product_sku"),
                product_image_url_snapshot=item.get("product_image_url"),
                quantity=item["quantity"],
                unit_price=item["unit_price"],
                unit_cost=item["unit_cost"],
                subtotal=item["subtotal"],
                subtotal_cost=item["subtotal_cost"],
                margin_amount=item["margin_amount"],
            )
            for item in total_data["items"]
        ]

        self.db.add_all(items)

        self.db.flush()
        self.db.refresh(db_obj)

        return db_obj

    def get_order_by_id(self, order_id: int) -> Optional[Order]:
        query = (
            select(Order)
            .options(
                selectinload(Order.items),
                selectinload(Order.client),
                selectinload(Order.client_branch),
                selectinload(Order.sales_rep),
                selectinload(Order.sales_invoice),
                selectinload(Order.sales_quote),
            )
            .where(Order.id == order_id)
        )
        return self.db.scalar(query)
    
    def get_order_by_id_for_update(
        self,
        order_id: int,
    ) -> Order | None:

        return (
            self.db.query(Order)
            .filter(Order.id == order_id)
            .with_for_update()
            .first()
        )

    def get_orders(
        self,
        *,
        status: Optional[str] = None,
        client_id: Optional[int] = None,
        sales_type: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[Order], int]:
        query = select(Order).options(
            selectinload(Order.items),
            selectinload(Order.client),
            selectinload(Order.client_branch),
            selectinload(Order.sales_rep),
            selectinload(Order.sales_invoice),
            selectinload(Order.sales_quote),
        )

        if status:
            query = query.where(Order.status == status)

        if client_id:
            query = query.where(Order.client_id == client_id)

        if sales_type:
            query = query.where(Order.sales_type == sales_type)

        count_query = select(func.count()).select_from(query.subquery())
        total = self.db.scalar(count_query) or 0

        query = query.order_by(Order.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)

        items = self.db.scalars(query).unique().all()

        return list(items), total
    
    def edit_order_shop(
        self,
        *,
        db_obj: Order,
        obj_in: OrderEditShop,
        total_data: dict | None,
    ) -> Order:
        if db_obj.status in ["delivered", "cancelled"]:
            raise ValueError(
                "No se puede editar esta orden"
            )

        if obj_in.customer_name is not None:
            db_obj.customer_name = obj_in.customer_name

        if obj_in.customer_phone is not None:
            db_obj.customer_phone = obj_in.customer_phone

        if obj_in.customer_email is not None:
            db_obj.customer_email = obj_in.customer_email

        if obj_in.delivery_type is not None:
            db_obj.delivery_type = obj_in.delivery_type

        if obj_in.delivery_address is not None:
            db_obj.delivery_address = obj_in.delivery_address

        if obj_in.delivery_city is not None:
            db_obj.delivery_city = obj_in.delivery_city

        if obj_in.delivery_reference is not None:
            db_obj.delivery_reference = obj_in.delivery_reference
            
        if obj_in.preferred_delivery_date is not None:
            db_obj.preferred_delivery_date = obj_in.preferred_delivery_date
            

        # Recalcular totales
        if total_data is not None:
            db_obj.total_amount = total_data["total_amount"]
            db_obj.total_cost = total_data["total_cost"]
            db_obj.margin_amount = total_data["margin_amount"]

            # Reemplazar items
            db_obj.items.clear()

            new_items = [
                OrderItem(
                    order_id=db_obj.id,
                    product_id=item["product_id"],
                    product_name_snapshot=item["product_name"],
                    product_brand_snapshot=item.get("product_brand"),
                    product_sku_snapshot=item.get("product_sku"),
                    product_image_url_snapshot=item.get("product_image_url"),
                    quantity=item["quantity"],
                    unit_price=item["unit_price"],
                    unit_cost=item["unit_cost"],
                    subtotal=item["subtotal"],
                    subtotal_cost=item["subtotal_cost"],
                    margin_amount=item["margin_amount"],
                )
                for item in total_data["items"]
            ]

            db_obj.items.extend(new_items)

        self.db.flush()
        self.db.refresh(db_obj)

        return db_obj
    
    def edit_order_b2b(
        self,
        *,
        db_obj: Order,
        obj_in: OrderEditB2B,
        total_data: dict | None,
    ) -> Order:
        if db_obj.status in ["delivered", "cancelled"]:
            raise ValueError(
                "No se puede editar esta orden"
            )

        if obj_in.client_branch_id is not None:
            db_obj.client_branch_id = obj_in.client_branch_id

        if obj_in.delivery_reference is not None:
            db_obj.delivery_reference = obj_in.delivery_reference
            

        if total_data is not None:
            db_obj.total_amount = total_data["total_amount"]
            db_obj.total_cost = total_data["total_cost"]
            db_obj.margin_amount = total_data["margin_amount"]

            db_obj.items.clear()

            new_items = [
                OrderItem(
                    order_id=db_obj.id,
                    product_id=item["product_id"],
                    product_name_snapshot=item["product_name"],
                    product_brand_snapshot=item.get("product_brand"),
                    product_sku_snapshot=item.get("product_sku"),
                    product_image_url_snapshot=item.get("product_image_url"),
                    quantity=item["quantity"],
                    unit_price=item["unit_price"],
                    unit_cost=item["unit_cost"],
                    subtotal=item["subtotal"],
                    subtotal_cost=item["subtotal_cost"],
                    margin_amount=item["margin_amount"],
                )
                for item in total_data["items"]
            ]

            db_obj.items.extend(new_items)

        self.db.flush()
        self.db.refresh(db_obj)

        return db_obj
    
    def update_order_shop(
        self,
        *,
        db_obj: Order,
        obj_in: OrderUpdateShop,
    ) -> Order:
        if db_obj.status in ["delivered", "cancelled"]:
            raise ValueError(
                "No se puede editar esta orden"
            )
            
        if obj_in.customer_name is not None:
            db_obj.customer_name = obj_in.customer_name

        if obj_in.customer_phone is not None:
            db_obj.customer_phone = obj_in.customer_phone

        if obj_in.customer_email is not None:
            db_obj.customer_email = obj_in.customer_email

        if obj_in.delivery_address is not None:
            db_obj.delivery_address = obj_in.delivery_address

        if obj_in.delivery_city is not None:
            db_obj.delivery_city = obj_in.delivery_city
            
        if obj_in.delivery_type is not None:
            db_obj.delivery_type = obj_in.delivery_type
            
        if obj_in.delivery_reference is not None:
            db_obj.delivery_reference = obj_in.delivery_reference

        if obj_in.document_type is not None:
            db_obj.document_type = obj_in.document_type

        self.db.flush()
        self.db.refresh(db_obj)

        return db_obj

    def update_order_b2b(
        self,
        *,
        db_obj: Order,
        obj_in: OrderUpdateB2B,
    ) -> Order:
        if db_obj.status in ["delivered", "cancelled"]:
            raise ValueError(
                "No se puede editar esta orden"
            )

        if (
            obj_in.client_branch_id is not None
            and obj_in.client_branch_id != db_obj.client_branch_id
        ):
            db_obj.client_branch_id = obj_in.client_branch_id

        if obj_in.document_type is not None:
            db_obj.document_type = obj_in.document_type

        self.db.flush()
        self.db.refresh(db_obj)

        return db_obj

    def update_order_status(
        self,
        *,
        db_obj: Order,
        obj_in: OrderUpdateStatus,
    ) -> Order:
        if obj_in.status == "delivered":
            if db_obj.scheduled_delivery_date is None:
                raise ValueError("La orden no tiene una entrega programada")

            db_obj.delivered_at = datetime.now(UTC)

        db_obj.status = obj_in.status

        self.db.flush()
        self.db.refresh(db_obj)

        return db_obj
    
    def schedule_delivery(
        self,
        *,
        db_obj: Order,
        scheduled_delivery_date: date,
    ) -> Order:
        if scheduled_delivery_date < date.today():
            raise ValueError(
                "La fecha programada no puede ser en el pasado"
            )

        if db_obj.status in ["cancelled", "delivered"]:
            raise ValueError(
                "No se puede programar la entrega de esta orden"
            )

        if db_obj.preferred_delivery_date:
            if scheduled_delivery_date < db_obj.preferred_delivery_date:
                raise ValueError(
                    "La fecha programada no puede ser anterior a la preferida"
                )

        db_obj.scheduled_delivery_date = scheduled_delivery_date

        self.db.flush()
        self.db.refresh(db_obj)

        return db_obj
    
    def mark_invoice_generated(
        self,
        *,
        db_obj: Order,
    ) -> Order:
        db_obj.invoice_generated = True

        self.db.flush()
        self.db.refresh(db_obj)

        return db_obj