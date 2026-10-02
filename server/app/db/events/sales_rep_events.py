from sqlalchemy import event
from app.models.sales_rep_model import SalesRep
from app.utils.geo import compute_h3

@event.listens_for(SalesRep, "before_insert")
@event.listens_for(SalesRep, "before_update")
def set_sales_rep_geo(mapper, connection, target):

    if target.home_lat is None or target.home_lng is None:
        target.home_h3_index = None
        return

    target.home_h3_index = compute_h3(
        target.home_lat,
        target.home_lng,
    )