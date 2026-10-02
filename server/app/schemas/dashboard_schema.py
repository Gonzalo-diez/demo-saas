from pydantic import BaseModel

class DashboardSummaryResponse(BaseModel):
    products_total: int
    clients_total: int
    orders_total: int
    sales_reps_total: int