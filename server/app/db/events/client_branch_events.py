from sqlalchemy import event
from app.models.client_branch_model import ClientBranch
from app.utils.geo import compute_h3

@event.listens_for(ClientBranch, "before_insert")
def set_h3_before_insert(mapper, connection, target):
    target.h3_index = compute_h3(target.lat, target.lng)

@event.listens_for(ClientBranch, "before_update")
def set_h3_before_update(mapper, connection, target):
    target.h3_index = compute_h3(target.lat, target.lng)